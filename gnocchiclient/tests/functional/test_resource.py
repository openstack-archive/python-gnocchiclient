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

from tempest_lib import exceptions

from gnocchiclient.tests.functional import base


class ResourceClientTest(base.ClientTestBase):
    RESOURCE_ID = str(uuid.uuid4())
    PROJECT_ID = str(uuid.uuid4())

    def details_multiple(self, output_lines, with_label=False):
        """Return list of dicts with item details from cli output tables.
        If with_label is True, key '__label' is added to each items dict.
        For more about 'label' see OutputParser.tables().

        NOTE(sileht): come from tempest-lib just because cliff use
        Field instead of Property as first columun header.
        """
        items = []
        tables_ = self.parser.tables(output_lines)
        for table_ in tables_:
            if ('Field' not in table_['headers']
                    or 'Value' not in table_['headers']):
                raise exceptions.InvalidStructure()
            item = {}
            for value in table_['values']:
                item[value[0]] = value[1]
            if with_label:
                item['__label'] = table_['label']
            items.append(item)
        return items

    def test_resource_scenario(self):
        # CREATE
        result = self.gnocchi(
            'resource', params="create generic -a id:%s" % self.RESOURCE_ID)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource["id"])
        self.assertEqual('None', resource["project_id"])
        self.assertNotEqual('None', resource["started_at"])

        # UPDATE
        result = self.gnocchi(
            'resource', params=("update generic %s -a project_id:%s" %
                                (self.RESOURCE_ID, self.PROJECT_ID)))
        resource_updated = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource_updated["id"])
        self.assertEqual(self.PROJECT_ID, resource_updated["project_id"])
        self.assertEqual(resource["started_at"],
                         resource_updated["started_at"])

        # GET
        result = self.gnocchi(
            'resource', params="show generic %s" % self.RESOURCE_ID)
        resource_got = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource_got["id"])
        self.assertEqual(self.PROJECT_ID, resource_got["project_id"])
        self.assertEqual(resource["started_at"], resource_got["started_at"])

        # LIST
        result = self.gnocchi('resource', params="list generic")
        self.assertIn(self.RESOURCE_ID,
                      [r['id'] for r in self.parser.listing(result)])
        resource_list = [r for r in self.parser.listing(result)
                         if r['id'] == self.RESOURCE_ID][0]
        self.assertEqual(self.RESOURCE_ID, resource_list["id"])
        self.assertEqual(self.PROJECT_ID, resource_list["project_id"])
        self.assertEqual(resource["started_at"], resource_list["started_at"])

        # DELETE
        result = self.gnocchi('resource',
                              params="delete %s" % self.RESOURCE_ID)
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('resource',
                              params="show generic %s" % self.RESOURCE_ID,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('resource',
                              params="delete %s" % self.RESOURCE_ID,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")

        # LIST EMPTY
        result = self.gnocchi('resource', params="list generic")
        self.assertNotIn(self.RESOURCE_ID,
                         [r['id'] for r in self.parser.listing(result)])
