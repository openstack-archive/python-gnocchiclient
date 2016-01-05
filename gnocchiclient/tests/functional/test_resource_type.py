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
    def test_resource_type_scenario(self):
        resource_type = ('ceph_account', 'network', 'instance', 'generic',
                         'ipmi, image', 'swift_account', 'volume',
                         'instance_network_interface',
                         'instance_disk', 'stack', 'identity')
        # LIST
        result = self.gnocchi(
            'resource-type', params="list")
        result_list = self.parser.listing(result)
        type_from_list = [t['result_type'] for t in result_list]
        self.assertEqual(resource_type, type_from_list)
