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
        resources = self.app.client.resource.list(
            resource_type=parsed_args.resource_type,
            **self._get_pagination_options(parsed_args))
        return utils.list2cols(self.COLS, resources)

    @staticmethod
    def _get_pagination_options(parsed_args):
        options = dict(
            details=parsed_args.details,
            sorts=parsed_args.sort,
            limit=parsed_args.limit,
            marker=parsed_args.marker)

        if hasattr(parsed_args, 'history'):
            options['history'] = parsed_args.history
        return options


class CliResourceHistory(CliResourceList):
    """Show the history of a resource"""

    def get_parser(self, prog_name):
        parser = super(CliResourceHistory, self).get_parser(prog_name,
                                                            history=False)
        parser.add_argument("resource_id",
                            help="ID of a resource")
        return parser

    def take_action(self, parsed_args):
        resources = self.app.client.resource.history(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id,
            **self._get_pagination_options(parsed_args))
        return utils.list2cols(self.COLS, resources)


class CliResourceSearch(CliResourceList):
    """Search resources with specified query rules"""

    def get_parser(self, prog_name):
        parser = super(CliResourceSearch, self).get_parser(prog_name)
        utils.add_query_argument("query", parser)
        return parser

    def take_action(self, parsed_args):
        resources = self.app.client.resource.search(
            resource_type=parsed_args.resource_type,
            query=parsed_args.query,
            **self._get_pagination_options(parsed_args))
        return utils.list2cols(self.COLS, resources)


def normalize_metrics(res):
    res['metrics'] = "\n".join(sorted(
        ["%s: %s" % (name, _id)
            for name, _id in res['metrics'].items()]))


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
        res = self.app.client.resource.get(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id)
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
                            help=("name and value of a attribute "
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
                r = self.app.client.resource.get(parsed_args.resource_type,
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
        res = self.app.client.resource.create(
            resource_type=parsed_args.resource_type, resource=resource)
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
        res = self.app.client.resource.update(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id,
            resource=resource)
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
        self.app.client.resource.delete(parsed_args.resource_id)


class CliResourceTypeList(lister.Lister):
    """List the resource types that gnocchi supports"""

    COLS = ('resource_type',
            'resource_controller_url')

    def take_action(self, parsed_args):
        resources = self.app.client.resource.list_types()
        return self.COLS, list(resources.items())
