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
        parser.add_argument("--resource", "-r", nargs=2,
                            metavar=("RESOURCE_ID", "METRIC_NAME"),
                            help="ID of the resource")
        return parser

    def take_action(self, parsed_args):
        metric = utils.dict_from_parsed_args(parsed_args,
                                             ["archive_policy_name"])
        kwds = {'metric': metric}
        if parsed_args.resource is not None:
            kwds['resource_id'] = parsed_args.resource[0]
            kwds['metric_name'] = parsed_args.resource[1]

        metric = self.app.client.metric.create(**kwds)
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
