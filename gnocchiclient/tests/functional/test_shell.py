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

import re


from gnocchiclient.tests.functional import base


class ResourceClientTest(base.ClientTestBase):
    def test_no_auth(self):
        result = self.gnocchi('resource', params="list", flags="--debug",
                              merge_stderr=True)
        endpoint = re.findall("(http://[^/]*)/v1/resource/generic",
                              result, re.M)[0]

        result = self.gnocchi('resource',
                              params="list",
                              flags=("--no-auth "
                                     "--endpoint %s") % endpoint,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Unauthorized (HTTP 401)")
