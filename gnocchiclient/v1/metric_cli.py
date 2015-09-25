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

from cliff import command
from cliff import lister
from cliff import show

from gnocchiclient import utils


class CliMetricList(lister.Lister):
    COLS = ('id', 'archive_policy/name', 'name', 'resource_id')

    def take_action(self, parsed_args):
        metrics = self.app.client.metric.list()
        for metric in metrics:
            utils.format_archive_policy(metric["archive_policy"])
            utils.format_move_dict_to_root(metric, "archive_policy")
        return utils.list2cols(self.COLS, metrics)


class CliMetricShow(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliMetricShow, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        parser.add_argument("resource_id", nargs='?',
                            help="ID of the resource")
        return parser

    def take_action(self, parsed_args):
        metric = self.app.client.metric.get(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id)
        utils.format_archive_policy(metric["archive_policy"])
        utils.format_move_dict_to_root(metric, "archive_policy")
        return self.dict2columns(metric)


class CliMetricCreate(show.ShowOne):

    def get_parser(self, prog_name):
        parser = super(CliMetricCreate, self).get_parser(prog_name)
        parser.add_argument("--archive-policy-name", "-a",
                            dest="archive_policy_name",
                            help=("name of the archive policy"))
        parser.add_argument("--resource-id", "-r",
                            dest="resource_id",
                            help="ID of the resource")
        parser.add_argument("name", nargs='?',
                            metavar="METRIC_NAME",
                            help="Name of the metric")
        return parser

    def take_action(self, parsed_args):
        metric = utils.dict_from_parsed_args(parsed_args,
                                             ["archive_policy_name",
                                              "name",
                                              "resource_id"])
        metric = self.app.client.metric.create(metric)
        utils.format_archive_policy(metric["archive_policy"])
        utils.format_move_dict_to_root(metric, "archive_policy")
        return self.dict2columns(metric)


class CliMetricDelete(command.Command):
    def get_parser(self, prog_name):
        parser = super(CliMetricDelete, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        parser.add_argument("resource_id", nargs='?',
                            help="ID of the resource")
        return parser

    def take_action(self, parsed_args):
        self.app.client.metric.delete(metric=parsed_args.metric,
                                      resource_id=parsed_args.resource_id)


class CliMeasuresGet(lister.Lister):
    COLS = ('timestamp', 'granularity', 'value')

    def get_parser(self, prog_name):
        parser = super(CliMeasuresGet, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        parser.add_argument("resource_id", nargs='?',
                            help="ID of the resource")
        parser.add_argument("--aggregation",
                            help="aggregation to retrieve")
        parser.add_argument("--start",
                            help="start of the period")
        parser.add_argument("--end",
                            help="end of the period")
        return parser

    def take_action(self, parsed_args):
        measures = self.app.client.metric.get_measures(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id,
            aggregation=parsed_args.aggregation,
            start=parsed_args.start,
            end=parsed_args.end,
        )
        return self.COLS, measures


class CliMeasuresAdd(command.Command):
    def measure(self, measure):
        timestamp, __, value = measure.rpartition("@")
        return {'timestamp': timestamp, 'value': float(value)}

    def get_parser(self, prog_name):
        parser = super(CliMeasuresAdd, self).get_parser(prog_name)
        parser.add_argument("metric",
                            help="ID or name of the metric")
        parser.add_argument("resource_id", nargs='?',
                            help="ID of the resource")
        parser.add_argument("-m", "--measure", action='append',
                            required=True, type=self.measure,
                            help=("timestamp and value of a measure "
                                  "separated with a '@'"))
        return parser

    def take_action(self, parsed_args):
        self.app.client.metric.add_measures(
            metric=parsed_args.metric,
            resource_id=parsed_args.resource_id,
            measures=parsed_args.measure,
        )


class CliMeasuresAggregation(lister.Lister):
    COLS = ('timestamp', 'granularity', 'value')

    def get_parser(self, prog_name):
        parser = super(CliMeasuresAggregation, self).get_parser(prog_name)
        parser.add_argument("-m", "--metric", nargs='+', required=True,
                            help="metrics IDs or metric name")
        parser.add_argument("--aggregation",
                            help="aggregation to retrieve")
        parser.add_argument("--start",
                            help="start of the period")
        parser.add_argument("--end",
                            help="end of the period")
        parser.add_argument("--needed-overlap", type=float,
                            help=("percent of datapoints in each "
                                  "metrics required"))
        parser.add_argument("--query", help="Query"),
        return parser

    def take_action(self, parsed_args):
        metrics = parsed_args.metric
        query = None
        if parsed_args.query:
            query = utils.search_query_builder(parsed_args.query)
            if len(parsed_args.metric) != 1:
                raise ValueError("One metric is required if query is provied")
            metrics = parsed_args.metric[0]
        measures = self.app.client.metric.aggregation(
            metrics=metrics,
            query=query,
            aggregation=parsed_args.aggregation,
            start=parsed_args.start,
            end=parsed_args.end,
            needed_overlap=parsed_args.needed_overlap,
        )
        return self.COLS, measures
