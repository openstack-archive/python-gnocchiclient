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

from gnocchiclient import exceptions
from gnocchiclient import utils


class CliResourceList(lister.Lister):
    """List resources"""

    COLS = ('id', 'type',
            'project_id', 'user_id',
            'original_resource_id',
            'started_at', 'ended_at',
            'revision_start', 'revision_end')

    def get_parser(self, prog_name, history=True):
        parser = super(CliResourceList, self).get_parser(prog_name)
        parser.add_argument("--details", action='store_true',
                            help="Show all attributes of generic resources"),
        if history:
            parser.add_argument("--history", action='store_true',
                                help="Show history of the resources"),
        parser.add_argument("--limit", type=int, metavar="<LIMIT>",
                            help="Number of resources to return "
                            "(Default is server default)")
        parser.add_argument("--marker", metavar="<MARKER>",
                            help="Last item of the previous listing. "
                            "Return the next results after this value")
        parser.add_argument("--sort", action="append", metavar="<SORT>",
                            help="Sort of resource attribute "
                            "(example: user_id:desc-nullslast")
        parser.add_argument("--type", "-t", dest="resource_type",
                            default="generic", help="Type of resource")
        return parser

    def take_action(self, parsed_args):
        resources = utils.get_client(self).resource.list(
            resource_type=parsed_args.resource_type,
            **utils.get_pagination_options(parsed_args))
        return utils.list2cols(self.COLS, resources)


class CliResourceHistory(CliResourceList):
    """Show the history of a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceHistory, self).get_parser(prog_name,
                                                            history=False)
        parser.add_argument("resource_id",
                            help="ID of a resource")
        return parser

    def take_action(self, parsed_args):
        resources = utils.get_client(self).resource.history(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id,
            **utils.get_pagination_options(parsed_args))
        cols = resources[0].keys() if resources else self.COLS
        if parsed_args.formatter == 'table':
            return utils.list2cols(cols, map(normalize_metrics, resources))
        return utils.list2cols(cols, resources)


class CliResourceSearch(CliResourceList):
    """Search resources with specified query rules"""

    def get_parser(self, prog_name):
        parser = super(CliResourceSearch, self).get_parser(prog_name)
        utils.add_query_argument("query", parser)
        return parser

    def take_action(self, parsed_args):
        resources = utils.get_client(self).resource.search(
            resource_type=parsed_args.resource_type,
            query=parsed_args.query,
            **utils.get_pagination_options(parsed_args))
        return utils.list2cols(self.COLS, resources)


def normalize_metrics(res):
    res['metrics'] = "\n".join(sorted(
        ["%s: %s" % (name, _id)
            for name, _id in res['metrics'].items()]))
    return res


class CliResourceShow(show.ShowOne):
    """Show a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceShow, self).get_parser(prog_name)
        parser.add_argument("--type", "-t", dest="resource_type",
                            default="generic", help="Type of resource")
        parser.add_argument("resource_id",
                            help="ID of a resource")
        return parser

    def take_action(self, parsed_args):
        res = utils.get_client(self).resource.get(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id)
        if parsed_args.formatter == 'table':
            normalize_metrics(res)
        return self.dict2columns(res)


class CliResourceCreate(show.ShowOne):
    """Create a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceCreate, self).get_parser(prog_name)
        parser.add_argument("--type", "-t", dest="resource_type",
                            default="generic", help="Type of resource")
        parser.add_argument("resource_id",
                            help="ID of the resource")
        parser.add_argument("-a", "--attribute", action='append',
                            default=[],
                            help=("name and value of an attribute "
                                  "separated with a ':'"))
        parser.add_argument("-m", "--add-metric", action='append',
                            default=[],
                            help="name:id of a metric to add"),
        parser.add_argument(
            "-n", "--create-metric", action='append', default=[],
            help="name:archive_policy_name of a metric to create"),
        return parser

    def _resource_from_args(self, parsed_args, update=False):
        resource = {}
        if not update:
            resource['id'] = parsed_args.resource_id
        if parsed_args.attribute:
            for attr in parsed_args.attribute:
                attr, __, value = attr.partition(":")
                resource[attr] = value
        if (parsed_args.add_metric
           or parsed_args.create_metric
           or (update and parsed_args.delete_metric)):
            if update:
                r = utils.get_client(self).resource.get(
                    parsed_args.resource_type,
                    parsed_args.resource_id)
                default = r['metrics']
                for metric_name in parsed_args.delete_metric:
                    try:
                        del default[metric_name]
                    except KeyError:
                        raise exceptions.MetricNotFound(
                            message="Metric name %s not found" % metric_name)
            else:
                default = {}
            resource['metrics'] = default
            for metric in parsed_args.add_metric:
                name, _, value = metric.partition(":")
                resource['metrics'][name] = value
            for metric in parsed_args.create_metric:
                name, _, value = metric.partition(":")
                if value is "":
                    resource['metrics'][name] = {}
                else:
                    resource['metrics'][name] = {'archive_policy_name': value}

        return resource

    def take_action(self, parsed_args):
        resource = self._resource_from_args(parsed_args)
        res = utils.get_client(self).resource.create(
            resource_type=parsed_args.resource_type, resource=resource)
        if parsed_args.formatter == 'table':
            normalize_metrics(res)
        return self.dict2columns(res)


class CliResourceUpdate(CliResourceCreate):
    """Update a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceUpdate, self).get_parser(prog_name)
        parser.add_argument("-d", "--delete-metric", action='append',
                            default=[],
                            help="Name of a metric to delete"),
        return parser

    def take_action(self, parsed_args):
        resource = self._resource_from_args(parsed_args, update=True)
        res = utils.get_client(self).resource.update(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id,
            resource=resource)
        if parsed_args.formatter == 'table':
            normalize_metrics(res)
        return self.dict2columns(res)


class CliResourceDelete(command.Command):
    """Delete a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceDelete, self).get_parser(prog_name)
        parser.add_argument("resource_id",
                            help="ID of the resource")
        return parser

    def take_action(self, parsed_args):
        utils.get_client(self).resource.delete(parsed_args.resource_id)


class CliResourceBatchDelete(show.ShowOne):
    """Delete a batch of resources based on attribute values"""

    def get_parser(self, prog_name):
        parser = super(CliResourceBatchDelete, self).get_parser(prog_name)
        parser.add_argument("--type", "-t", dest="resource_type",
                            default="generic", help="Type of resource")
        utils.add_query_argument("query", parser)
        return parser

    def take_action(self, parsed_args):
        res = utils.get_client(self).resource.batch_delete(
            resource_type=parsed_args.resource_type,
            query=parsed_args.query)
        return self.dict2columns(res)
