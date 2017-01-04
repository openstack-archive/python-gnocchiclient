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

from oslo_utils import uuidutils

from gnocchiclient.tests.functional import base


class ResourceTypeClientTest(base.ClientTestBase):
    RESOURCE_TYPE = uuidutils.generate_uuid()
    RESOURCE_ID = uuidutils.generate_uuid()

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

        # PATCH
        result = self.gnocchi(
            u'resource-type',
            params=u"update -r foo "
            "-a new:number:no:max=16 %s" % self.RESOURCE_TYPE)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_TYPE, resource["name"])
        self.assertNotIn("attributes/foo", resource)
        self.assertEqual(
            "max=16, min=None, required=False, type=number",
            resource["attributes/new"])

        # SHOW
        result = self.gnocchi(
            u'resource-type', params=u"show %s" % self.RESOURCE_TYPE)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_TYPE, resource["name"])
        self.assertNotIn("attributes/foo", resource)
        self.assertEqual(
            "max=16, min=None, required=False, type=number",
            resource["attributes/new"])

        # Create a resource for this type
        result = self.gnocchi(
            u'resource', params=(u"create %s -t %s -a new:5") %
            (self.RESOURCE_ID, self.RESOURCE_TYPE))
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource["id"])
        self.assertEqual('5.0', resource["new"])

        # Delete the resource
        self.gnocchi('resource', params="delete %s" % self.RESOURCE_ID)

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
