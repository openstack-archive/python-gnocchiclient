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


class CliResourceTypeList(lister.Lister):
    """List the resource types that gnocchi supports"""
    COLS = ('resource_type',
            'resource_controller_url')

    def take_action(self, parsed_args):
        resources = self.app.client.resource_type.list()
        return self.COLS, list(resources.items())
