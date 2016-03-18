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


class ArchivePolicyClientTest(base.ClientTestBase):
    def test_archive_policy_scenario(self):
        # CREATE
        apname = str(uuid.uuid4())
        result = self.gnocchi(
            u'archive-policy', params=u"create %s"
            u" --back-window 0"
            u" -d granularity:1s,points:86400" % apname)
        policy = self.details_multiple(result)[0]
        self.assertEqual(apname, policy["name"])

        # CREATE FAIL
        result = self.gnocchi(
            u'archive-policy', params=u"create %s"
            u" --back-window 0"
            u" -d granularity:1s,points:86400" % apname,
            fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy %s already exists (HTTP 409)" % apname)

        # GET
        result = self.gnocchi(
            'archive-policy', params="show %s" % apname)
        policy = self.details_multiple(result)[0]
        self.assertEqual(apname, policy["name"])

        # LIST
        result = self.gnocchi(
            'archive-policy', params="list")
        policies = self.parser.listing(result)
        policy_from_list = [p for p in policies
                            if p['name'] == apname][0]
        for field in ["back_window", "definition", "aggregation_methods"]:
            self.assertEqual(policy[field], policy_from_list[field])

        # DELETE
        result = self.gnocchi('archive-policy',
                              params="delete %s" % apname)
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('archive-policy',
                              params="show %s" % apname,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy %s does not exist (HTTP 404)" % apname)

        # DELETE FAIL
        result = self.gnocchi('archive-policy',
                              params="delete %s" % apname,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Archive policy %s does not exist (HTTP 404)" % apname)
