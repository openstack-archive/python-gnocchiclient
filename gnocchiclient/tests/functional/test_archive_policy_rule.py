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


class ArchivePolicyRuleClientTest(base.ClientTestBase):
    def test_archive_policy_rule_scenario(self):
        apname = str(uuid.uuid4())
        # Create an archive policy
        self.gnocchi(
            u'archive-policy', params=u"create %s"
            u" -d granularity:1s,points:86400" % apname)

        # CREATE
        result = self.gnocchi(
            u'archive-policy-rule', params=u"create test"
            u" --archive-policy-name %s"
            u" --metric-pattern 'disk.io.*'" % apname)
        policy_rule = self.details_multiple(result)[0]
        self.assertEqual('test', policy_rule["name"])

        # CREATE FAIL
        result = self.gnocchi(
            u'archive-policy-rule', params=u"create test"
            u" --archive-policy-name high"
            u" --metric-pattern 'disk.io.*'",
            fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy rule test already exists (HTTP 409)")
        # GET
        result = self.gnocchi(
            'archive-policy-rule', params="show test")
        policy_rule = self.details_multiple(result)[0]
        self.assertEqual("test", policy_rule["name"])

        # LIST
        result = self.gnocchi('archive-policy-rule', params="list")
        rules = self.parser.listing(result)
        rule_from_list = [p for p in rules
                          if p['name'] == 'test'][0]
        for field in ["metric_pattern", "archive_policy_name"]:
            self.assertEqual(policy_rule[field], rule_from_list[field])

        # DELETE
        result = self.gnocchi('archive-policy-rule',
                              params="delete test")
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('archive-policy-rule',
                              params="show test",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy rule test does not exist (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('archive-policy-rule',
                              params="delete test",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy rule test does not exist (HTTP 404)")
