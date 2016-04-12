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

from gnocchiclient.tests.functional import base


class ResourceTypeClientTest(base.ClientTestBase):

    def test_help(self):
        self.gnocchi("help", params="resource list")

    def test_resource_type_scenario(self):
        # LIST
        result = self.gnocchi('resource-type', params="list")
        r = self.parser.listing(result)
        self.assertEqual([{'attributes': '', 'name': 'generic'}], r)
