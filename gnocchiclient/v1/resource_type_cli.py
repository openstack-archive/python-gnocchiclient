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

from gnocchiclient import utils


class CliResourceTypeList(lister.Lister):
    """List resource types"""

    COLS = ('name', 'attributes')

    def take_action(self, parsed_args):
        resource_types = self.app.client.resource_type.list()
        for resource_type in resource_types:
            utils.format_dict_dict(resource_type, 'attributes')
        return utils.list2cols(self.COLS, resource_types)
