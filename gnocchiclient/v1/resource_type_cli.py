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
from cliff import lister
from cliff import show

from gnocchiclient import utils


class CliResourceTypeList(lister.Lister):
    """List resource types"""

    COLS = ('name', 'attributes')

    def take_action(self, parsed_args):
        resource_types = self.app.client.resource_type.list()
        for resource_type in resource_types:
            utils.format_dict_dict(resource_type, 'attributes')
        return utils.list2cols(self.COLS, resource_types)


class CliResourceTypeCreate(show.ShowOne):
    """Create a resource type"""

    def get_parser(self, prog_name):
        parser = super(CliResourceTypeCreate, self).get_parser(prog_name)
        parser.add_argument("name", help="name of the resource type")
        parser.add_argument("-a", "--attribute", action='append',
                            type=self._resource_attribute,
                            default=[],
                            help=("name, type, requirement and options of a "
                                  "attribute separated with ':'. For example: "
                                  "display_name:string:true:max_length=255"))
        return parser

    @staticmethod
    def _resource_attribute(value):
        config = value.split(":")
        name = config.pop(0)
        attrs = {}
        if config:
            attrs["type"] = config.pop(0)
        if config:
            attrs["required"] = bool(config.pop(0))
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
        res = self.app.client.resource_type.create(resource_type=resource_type)
        utils.format_resource_type(res)
        return self.dict2columns(res)
