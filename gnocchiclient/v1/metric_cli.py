#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import sys

from cliff import command
from cliff import lister
from cliff import show

from gnocchiclient import utils


class CliMetricWithResourceID(command.Command):
    def get_parser(self, prog_name):
        parser = super(CliMetricWithResourceID, self).get_parser(prog_name)
        parser.add_argument("--resource-id", "-r",
                            help="ID of the resource")
        return parser


class CliMetricList(lister.Lister):
    """List metrics"""

    COLS = ('id', 'archive_policy/name', 'name', 'resource_id')

    def take_action(self, parsed_args):
        metrics = utils.get_client(self).metric.list()
        for metric in metrics:
            utils.format_archive_policy(metric["archive_policy"])
            utils.format_move_dict_to_root(metric, "archive_policy")
        return utils.list2cols(self.COLS, metrics)


class CliMetricShow(CliMetricWithResourceID, show.ShowOne):
    """Show a metric"""

    def get_parser(self, prog_name):
        parser = super(CliMetricShow, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        return parser

    def take_action(self, parsed_args):
        metric = utils.get_client(self).metric.get(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id)
        utils.format_archive_policy(metric["archive_policy"])
        utils.format_move_dict_to_root(metric, "archive_policy")
        utils.format_resource_for_metric(metric)
        return self.dict2columns(metric)


class CliMetricCreateBase(show.ShowOne, CliMetricWithResourceID):
    def get_parser(self, prog_name):
        parser = super(CliMetricCreateBase, self).get_parser(prog_name)
        parser.add_argument("--archive-policy-name", "-a",
                            dest="archive_policy_name",
                            help="name of the archive policy")
        return parser

    def take_action(self, parsed_args):
        metric = utils.dict_from_parsed_args(parsed_args,
                                             ["archive_policy_name",
                                              "resource_id"])
        return self._take_action(metric, parsed_args)


class CliMetricCreate(CliMetricCreateBase):
    """Create a metric"""

    def get_parser(self, prog_name):
        parser = super(CliMetricCreate, self).get_parser(prog_name)
        parser.add_argument("name", nargs='?',
                            metavar="METRIC_NAME",
                            help="Name of the metric")
        return parser

    def _take_action(self, metric, parsed_args):
        if parsed_args.name:
            metric['name'] = parsed_args.name
        metric = utils.get_client(self).metric.create(metric)
        utils.format_archive_policy(metric["archive_policy"])
        utils.format_move_dict_to_root(metric, "archive_policy")
        utils.format_resource_for_metric(metric)
        return self.dict2columns(metric)


class CliMetricDelete(CliMetricWithResourceID):
    """Delete a metric"""

    def get_parser(self, prog_name):
        parser = super(CliMetricDelete, self).get_parser(prog_name)
        parser.add_argument("metric", nargs='+',
                            help="IDs or names of the metric")
        return parser

    def take_action(self, parsed_args):
        for metric in parsed_args.metric:
            utils.get_client(self).metric.delete(
                metric=metric, resource_id=parsed_args.resource_id)


class CliMeasuresShow(CliMetricWithResourceID, lister.Lister):
    """Get measurements of a metric"""

    COLS = ('timestamp', 'granularity', 'value')

    def get_parser(self, prog_name):
        parser = super(CliMeasuresShow, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        parser.add_argument("--aggregation",
                            help="aggregation to retrieve")
        parser.add_argument("--start",
                            help="beginning of the period")
        parser.add_argument("--stop",
                            help="end of the period")
        parser.add_argument("--granularity",
                            help="granularity to retrieve (in seconds)")
        return parser

    def take_action(self, parsed_args):
        measures = utils.get_client(self).metric.get_measures(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id,
            aggregation=parsed_args.aggregation,
            start=parsed_args.start,
            stop=parsed_args.stop,
            granularity=parsed_args.granularity,
        )
        return self.COLS, measures


class CliMeasuresAddBase(CliMetricWithResourceID):
    def get_parser(self, prog_name):
        parser = super(CliMeasuresAddBase, self).get_parser(prog_name)
        parser.add_argument("metric", help="ID or name of the metric")
        return parser


class CliMeasuresAdd(CliMeasuresAddBase):
    """Add measurements to a metric"""

    def measure(self, measure):
        timestamp, __, value = measure.rpartition("@")
        return {'timestamp': timestamp, 'value': float(value)}

    def get_parser(self, prog_name):
        parser = super(CliMeasuresAdd, self).get_parser(prog_name)
        parser.add_argument("-m", "--measure", action='append',
                            required=True, type=self.measure,
                            help=("timestamp and value of a measure "
                                  "separated with a '@'"))
        return parser

    def take_action(self, parsed_args):
        utils.get_client(self).metric.add_measures(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id,
            measures=parsed_args.measure,
        )


class CliMeasuresBatch(command.Command):
    def stdin_or_file(self, value):
        if value == "-":
            return sys.stdin
        else:
            return open(value, 'r')

    def get_parser(self, prog_name):
        parser = super(CliMeasuresBatch, self).get_parser(prog_name)
        parser.add_argument("file", type=self.stdin_or_file,
                            help=("File containing measurements to batch or "
                                  "- for stdin (see Gnocchi REST API docs for "
                                  "the format"))
        return parser


class CliMetricsMeasuresBatch(CliMeasuresBatch):
    def take_action(self, parsed_args):
        with parsed_args.file as f:
            utils.get_client(self).metric.batch_metrics_measures(json.load(f))


class CliResourcesMetricsMeasuresBatch(CliMeasuresBatch):
    def take_action(self, parsed_args):
        with parsed_args.file as f:
            utils.get_client(self).metric.batch_resources_metrics_measures(
                json.load(f))


class CliMeasuresAggregation(lister.Lister):
    """Get measurements of aggregated metrics"""

    COLS = ('timestamp', 'granularity', 'value')

    def get_parser(self, prog_name):
        parser = super(CliMeasuresAggregation, self).get_parser(prog_name)
        parser.add_argument("-m", "--metric", nargs='+', required=True,
                            help="metrics IDs or metric name")
        parser.add_argument("--aggregation",
                            help="aggregation to retrieve")
        parser.add_argument("--start",
                            help="beginning of the period")
        parser.add_argument("--stop",
                            help="end of the period")
        parser.add_argument("--needed-overlap", type=float,
                            help=("percent of datapoints in each "
                                  "metrics required"))
        utils.add_query_argument("--query", parser)
        parser.add_argument("--resource-type", default="generic",
                            help="Resource type to query"),
        parser.add_argument("--groupby",
                            action='append',
                            help="Attribute to use to group resources"),
        return parser

    def take_action(self, parsed_args):
        metrics = parsed_args.metric
        if parsed_args.query:
            if len(parsed_args.metric) != 1:
                raise ValueError("One metric is required if query is provided")
            metrics = parsed_args.metric[0]
        measures = utils.get_client(self).metric.aggregation(
            metrics=metrics,
            query=parsed_args.query,
            aggregation=parsed_args.aggregation,
            start=parsed_args.start,
            stop=parsed_args.stop,
            needed_overlap=parsed_args.needed_overlap,
            resource_type=parsed_args.resource_type,
            groupby=parsed_args.groupby,
        )
        if parsed_args.groupby:
            ms = []
            for g in measures:
                group_name = ", ".join("%s: %s" % (k, g['group'][k])
                                       for k in sorted(g['group']))
                for m in g['measures']:
                    i = [group_name]
                    i.extend(m)
                    ms.append(i)
            return ('group',) + self.COLS, ms
        return self.COLS, measures
