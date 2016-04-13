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

import uuid

from gnocchiclient.tests.functional import base


class ResourceTypeClientTest(base.ClientTestBase):
    RESOURCE_TYPE = str(uuid.uuid4())

    def test_help(self):
        self.gnocchi("help", params="resource list")

    def test_resource_type_scenario(self):
        # LIST
        result = self.gnocchi('resource-type', params="list")
        r = self.parser.listing(result)
        self.assertEqual([{'attributes': '', 'name': 'generic'}], r)

        # CREATE
        result = self.gnocchi(
            u'resource-type',
            params=u"create -a foo:string:1:max_length=16 "
                   "-a bar:number:no:max=32 %s" % self.RESOURCE_TYPE)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_TYPE, resource["name"])
        self.assertEqual(
            "max_length=16, min_length=0, required=True, type=string",
            resource["attributes/foo"])

        # SHOW
        result = self.gnocchi(
            u'resource-type', params=u"show %s" % self.RESOURCE_TYPE)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_TYPE, resource["name"])
        self.assertEqual(
            "max_length=16, min_length=0, required=True, type=string",
            resource["attributes/foo"])

        # DELETE
        result = self.gnocchi('resource-type',
                              params="delete %s" % self.RESOURCE_TYPE)
        self.assertEqual("", result)

        # DELETE AGAIN
        result = self.gnocchi('resource-type',
                              params="delete %s" % self.RESOURCE_TYPE,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource type %s does not exist (HTTP 404)" % self.RESOURCE_TYPE)

        # SHOW AGAIN
        result = self.gnocchi(u'resource-type',
                              params=u"show %s" % self.RESOURCE_TYPE,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource type %s does not exist (HTTP 404)" % self.RESOURCE_TYPE)
