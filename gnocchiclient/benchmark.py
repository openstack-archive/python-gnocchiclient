# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import argparse
import datetime
import functools
import logging
import random
import time
import types

from cliff import show
import futurist
from oslo_utils import timeutils
import six.moves

from gnocchiclient.v1 import metric_cli

LOG = logging.getLogger(__name__)


def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

six.moves.copyreg.pickle(types.MethodType, _pickle_method)


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF
    args = [iter(iterable)] * n
    return six.moves.zip(*args)


def _positive_non_zero_int(argument_value):
    if argument_value is None:
        return None
    try:
        value = int(argument_value)
    except ValueError:
        msg = "%s must be an integer" % argument_value
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % argument_value
        raise argparse.ArgumentTypeError(msg)
    return value


class BenchmarkPool(futurist.ProcessPoolExecutor):
    def submit_job(self, times, fn, *args, **kwargs):
        self.sw = timeutils.StopWatch()
        self.sw.start()
        self.times = times
        return [self.submit(fn, *args, **kwargs)
                for i in six.moves.range(times)]

    def map_job(self, fn, iterable, **kwargs):
        self.sw = timeutils.StopWatch()
        self.sw.start()
        r = []
        self.times = 0
        for item in iterable:
            r.append(self.submit(fn, item, **kwargs))
            self.times += 1
        return r

    def _log_progress(self, verb):
        runtime = self.sw.elapsed()
        done = self.statistics.executed
        rate = done / runtime if runtime != 0 else 0
        LOG.info(
            "%d/%d, "
            "total: %.2f seconds, "
            "rate: %.2f %s/second"
            % (done, self.times, runtime, rate, verb))

    def wait_job(self, verb, futures):
        while self.statistics.executed != self.times:
            self._log_progress(verb)
            time.sleep(1)
        self._log_progress(verb)
        self.shutdown(wait=True)
        runtime = self.sw.elapsed()
        results = []
        for f in futures:
            try:
                results.append(f.result())
            except Exception as e:
                LOG.error("Error with %s metric: %s" % (verb, e))
        return results, runtime, {
            'client workers': self._max_workers,
            verb + ' runtime': "%.2f seconds" % runtime,
            verb + ' executed': self.statistics.executed,
            verb + ' speed': (
                "%.2f %s/s" % (self.statistics.executed / runtime, verb)
            ),
            verb + ' failures': self.statistics.failures,
            verb + ' failures rate': (
                "%.2f %%" % (
                    100
                    * self.statistics.failures
                    / float(self.statistics.executed)
                )
            ),
        }


class CliBenchmarkBase(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkBase, self).get_parser(prog_name)
        parser.add_argument("--workers", "-w",
                            default=None,
                            type=_positive_non_zero_int,
                            help="Number of workers to use")
        return parser


class CliBenchmarkMetricShow(CliBenchmarkBase,
                             metric_cli.CliMetricWithResourceID):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkMetricShow, self).get_parser(prog_name)
        parser.add_argument("metric", nargs='+',
                            help="ID or name of the metrics")
        parser.add_argument("--count", "-n",
                            required=True,
                            type=_positive_non_zero_int,
                            help="Number of metrics to get")
        return parser

    def take_action(self, parsed_args):
        pool = BenchmarkPool(parsed_args.workers)
        LOG.info("Getting metrics")
        futures = pool.map_job(self.app.client.metric.get,
                               parsed_args.metric * parsed_args.count,
                               resource_id=parsed_args.resource_id)
        result, runtime, stats = pool.wait_job("show", futures)
        return self.dict2columns(stats)


class CliBenchmarkMetricCreate(CliBenchmarkBase,
                               metric_cli.CliMetricCreateBase):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkMetricCreate, self).get_parser(prog_name)
        parser.add_argument("--count", "-n",
                            required=True,
                            type=_positive_non_zero_int,
                            help="Number of metrics to create")
        parser.add_argument("--keep", "-k",
                            action='store_true',
                            help="Keep created metrics")
        return parser

    def _take_action(self, metric, parsed_args):
        pool = BenchmarkPool(parsed_args.workers)

        LOG.info("Creating metrics")
        futures = pool.submit_job(parsed_args.count,
                                  self.app.client.metric.create,
                                  metric, refetch_metric=False)
        created_metrics, runtime, stats = pool.wait_job("create", futures)

        if not parsed_args.keep:
            LOG.info("Deleting metrics")
            pool = BenchmarkPool(parsed_args.workers)
            futures = pool.map_job(self.app.client.metric.delete,
                                   [m['id'] for m in created_metrics])
            _, runtime, dstats = pool.wait_job("delete", futures)
            stats.update(dstats)

        return self.dict2columns(stats)


class CliBenchmarkMeasuresAdd(CliBenchmarkBase,
                              metric_cli.CliMeasuresAddBase):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkMeasuresAdd, self).get_parser(prog_name)
        parser.add_argument("--count", "-n",
                            required=True,
                            type=_positive_non_zero_int,
                            help="Number of total measures to send")
        parser.add_argument("--batch", "-b",
                            default=1,
                            type=_positive_non_zero_int,
                            help="Number of measures to send in each batch")
        parser.add_argument("--timestamp-start", "-s",
                            default=(
                                timeutils.utcnow(True)
                                - datetime.timedelta(days=365)),
                            type=timeutils.parse_isotime,
                            help="First timestamp to use")
        parser.add_argument("--timestamp-end", "-e",
                            default=timeutils.utcnow(True),
                            type=timeutils.parse_isotime,
                            help="Last timestamp to use")
        return parser

    def take_action(self, parsed_args):
        pool = BenchmarkPool(parsed_args.workers)
        LOG.info("Sending measures")

        if parsed_args.timestamp_end <= parsed_args.timestamp_start:
            raise ValueError("End timestamp must be after start timestamp")

        # If batch size is bigger than the number of measures to send, we
        # reduce it to make sure we send something.
        if parsed_args.batch > parsed_args.count:
            parsed_args.batch = parsed_args.count

        start = int(parsed_args.timestamp_start.strftime("%s"))
        end = int(parsed_args.timestamp_end.strftime("%s"))
        count = parsed_args.count

        if (end - start) < count:
            raise ValueError(
                "The specified time range is not large enough "
                "for the number of points")

        random_values = (random.randint(- 2 ** 32, 2 ** 32)
                         for _ in six.moves.range(count))
        all_measures = ({"timestamp": ts, "value": v}
                        for ts, v
                        in six.moves.zip(
                            six.moves.range(start,
                                            end,
                                            (end - start) // count),
                            random_values))

        measures = grouper(all_measures, parsed_args.batch)

        futures = pool.map_job(functools.partial(
            self.app.client.metric.add_measures,
            parsed_args.metric), measures, resource_id=parsed_args.resource_id)
        _, runtime, stats = pool.wait_job("push", futures)

        stats['measures per request'] = parsed_args.batch
        stats['measures push speed'] = (
            "%.2f push/s" % (
                parsed_args.batch * pool.statistics.executed / runtime
            )
        )

        return self.dict2columns(stats)


class CliBenchmarkMeasuresShow(CliBenchmarkBase,
                               metric_cli.CliMeasuresShow):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkMeasuresShow, self).get_parser(prog_name)
        parser.add_argument("--count", "-n",
                            required=True,
                            type=_positive_non_zero_int,
                            help="Number of total measures to send")
        return parser

    def take_action(self, parsed_args):
        pool = BenchmarkPool(parsed_args.workers)
        LOG.info("Getting measures")
        futures = pool.submit_job(parsed_args.count,
                                  self.app.client.metric.get_measures,
                                  metric=parsed_args.metric,
                                  resource_id=parsed_args.resource_id,
                                  aggregation=parsed_args.aggregation,
                                  start=parsed_args.start,
                                  end=parsed_args.end)
        result, runtime, stats = pool.wait_job("show", futures)
        return self.dict2columns(stats)
