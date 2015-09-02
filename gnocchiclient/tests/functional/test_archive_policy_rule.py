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

from tempest_lib import exceptions

from gnocchiclient.tests.functional import base


class ArchivePolicyRuleClientTest(base.ClientTestBase):

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

    def test_archive_policy_rule_scenario(self):
        # CREATE
        result = self.gnocchi(
            u'archivepolicyrule', params=u"create -a name:test"
                                         u" -a archive_policy_name:high"
                                         u" -a metric_pattern:disk.io.*")
        policy_rule = self.details_multiple(result)[0]
        self.assertEqual('test', policy_rule["name"])

        # GET
        result = self.gnocchi(
            'archivepolicyrule', params="show test")
        policy_rule = self.details_multiple(result)[0]
        self.assertEqual("test", policy_rule["name"])

        # DELETE
        result = self.gnocchi('archivepolicyrule',
                              params="delete test")
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('archivepolicyrule',
                              params="show test",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('archivepolicyrule',
                              params="delete test",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")
