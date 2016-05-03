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
from oslo_utils import strutils

from gnocchiclient import utils


class CliResourceTypeList(lister.Lister):
    """List resource types"""

    COLS = ('name', 'attributes')

    def take_action(self, parsed_args):
        resource_types = utils.get_client(self).resource_type.list()
        for resource_type in resource_types:
            resource_type['attributes'] = utils.format_dict_dict(
                resource_type['attributes'])
        return utils.list2cols(self.COLS, resource_types)


class CliResourceTypeCreate(show.ShowOne):
    """Create a resource type"""

    def get_parser(self, prog_name):
        parser = super(CliResourceTypeCreate, self).get_parser(prog_name)
        parser.add_argument("name", help="name of the resource type")
        parser.add_argument("-a", "--attribute", action='append',
                            type=self._resource_attribute,
                            default=[],
                            help=(u"attribute definition, "
                                  u"attribute_name:"
                                  u"attribute_type:"
                                  u"attribute_is_required:"
                                  u"attribute_type_option_name="
                                  u"attribute_type_option_value:\u2026 "
                                  u"For example: "
                                  u"display_name:string:true:max_length=255"))
        return parser

    @classmethod
    def _resource_attribute(cls, value):
        config = value.split(":")
        name = config.pop(0)
        attrs = {}
        if config:
            attrs["type"] = config.pop(0)
        if config:
            attrs["required"] = strutils.bool_from_string(config.pop(0),
                                                          strict=True)
        while config:
            param, _, value = config.pop(0).partition("=")
            try:
                attrs[param] = int(value)
            except ValueError:
                try:
                    attrs[param] = float(value)
                except ValueError:
                    attrs[param] = value
        return (name, attrs)

    def take_action(self, parsed_args):
        resource_type = {'name': parsed_args.name}
        if parsed_args.attribute:
            resource_type['attributes'] = dict(parsed_args.attribute)
        res = utils.get_client(self).resource_type.create(
            resource_type=resource_type)
        utils.format_resource_type(res)
        return self.dict2columns(res)


class CliResourceTypeShow(show.ShowOne):
    """Show a resource type"""

    def get_parser(self, prog_name):
        parser = super(CliResourceTypeShow, self).get_parser(prog_name)
        parser.add_argument("name", help="name of the resource type")
        return parser

    def take_action(self, parsed_args):
        res = utils.get_client(self).resource_type.get(name=parsed_args.name)
        utils.format_resource_type(res)
        return self.dict2columns(res)


class CliResourceTypeDelete(command.Command):
    """Delete a resource type"""

    def get_parser(self, prog_name):
        parser = super(CliResourceTypeDelete, self).get_parser(prog_name)
        parser.add_argument("name", help="name of the resource type")
        return parser

    def take_action(self, parsed_args):
        utils.get_client(self).resource_type.delete(parsed_args.name)
