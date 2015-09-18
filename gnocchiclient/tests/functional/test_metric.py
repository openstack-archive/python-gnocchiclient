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


class MetricClientTest(base.ClientTestBase):
    def test_metric_scenario(self):
        # PREPARE AN ACHIVE POLICY
        self.gnocchi(
            u'archive policy', params=u"create metric-test"
            u" --back-window 0"
            u" -d granularity:1s,points:86400")

        # CREATE
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual(self.clients.project_id,
                         metric["created_by_project_id"])
        self.assertEqual(self.clients.user_id, metric["created_by_user_id"])
        self.assertEqual('None', metric["name"])
        self.assertEqual('None', metric["resource"])
        self.assertIn("metric-test", metric["archive_policy/name"])

        # GET
        result = self.gnocchi('metric', params="show %s" % metric["id"])
        metric_get = self.details_multiple(result)[0]
        self.assertEqual(metric, metric_get)

        # LIST
        result = self.gnocchi('metric', params="list")
        metrics = self.parser.listing(result)
        metric_from_list = [p for p in metrics
                            if p['archive_policy/name'] == 'metric-test'][0]
        for field in ["archive_policy/name", "name"]:
            # FIXME(sileht): add "resource_id" or "resource"
            # when LP#1497171 is fixed
            self.assertEqual(metric[field], metric_from_list[field])

        # DELETE
        result = self.gnocchi('metric', params="delete %s" % metric["id"])
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('metric', params="show %s" % metric["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('metric', params="delete %s" % metric["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")
