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
import logging
import time

from cliff import show
import futurist
from oslo_utils import timeutils
import six.moves

from gnocchiclient.v1 import metric_cli

LOG = logging.getLogger(__name__)


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


class BenchmarkPool(futurist.ThreadPoolExecutor):
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
        return results, {
            'client workers': self._max_workers,
            verb + ' runtime': "%.2f seconds" % runtime,
            verb + ' executed': self.statistics.executed,
            verb + ' speed': (
                "%.2f metric/s" % (self.statistics.executed / runtime)
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
        parser.add_argument("--number", "-n",
                            required=True,
                            type=_positive_non_zero_int,
                            help="Number of metrics to get")
        return parser

    def take_action(self, parsed_args):
        pool = BenchmarkPool(parsed_args.workers)
        LOG.info("Getting metrics")
        futures = pool.map_job(self.app.client.metric.get,
                               parsed_args.metric * parsed_args.number,
                               resource_id=parsed_args.resource_id)
        result, stats = pool.wait_job("show", futures)
        return self.dict2columns(stats)


class CliBenchmarkMetricCreate(CliBenchmarkBase,
                               metric_cli.CliMetricCreateBase):
    def get_parser(self, prog_name):
        parser = super(CliBenchmarkMetricCreate, self).get_parser(prog_name)
        parser.add_argument("--number", "-n",
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
        futures = pool.submit_job(parsed_args.number,
                                  self.app.client.metric.create,
                                  metric, refetch_metric=False)
        created_metrics, stats = pool.wait_job("create", futures)

        if not parsed_args.keep:
            LOG.info("Deleting metrics")
            pool = BenchmarkPool(parsed_args.workers)
            futures = pool.map_job(self.app.client.metric.delete,
                                   [m['id'] for m in created_metrics])
            _, dstats = pool.wait_job("delete", futures)
            stats.update(dstats)

        return self.dict2columns(stats)
