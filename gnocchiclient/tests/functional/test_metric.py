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
        self.gnocchi("archive-policy", params="create metric-test "
                     "--back-window 0 -d granularity:1s,points:86400")

        # CREATE WITH NAME
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test some-name")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual(self.clients.project_id,
                         metric["created_by_project_id"])
        self.assertEqual(self.clients.user_id, metric["created_by_user_id"])
        self.assertEqual('some-name', metric["name"])
        self.assertEqual('None', metric["resource"])
        self.assertIn("metric-test", metric["archive_policy/name"])

        # CREATE WITHOUT NAME
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

        # MEASURES ADD
        result = self.gnocchi('measures',
                              params=("add %s "
                                      "-m '2015-03-06T14:33:57@43.11' "
                                      "--measure '2015-03-06T14:34:12@12' "
                                      ) % metric["id"])
        self.assertEqual("", result)

        # MEASURES GET
        result = self.retry_gnocchi(
            5, 'measures', params=("get %s "
                                   "--aggregation mean "
                                   "--start 2015-03-06T14:32:00 "
                                   "--end 2015-03-06T14:36:00"
                                   ) % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES AGGREGATION
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--metric %s "
                                "--aggregation mean "
                                "--start 2015-03-06T14:32:00 "
                                "--end 2015-03-06T14:36:00"
                                ) % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # LIST
        result = self.gnocchi('metric', params="list")
        metrics = self.parser.listing(result)
        metric_from_list = [p for p in metrics
                            if p['id'] == metric['id']][0]
        for field in ["id", "archive_policy/name", "name"]:
            # FIXME(sileht): add "resource_id" or "resource"
            # when LP#1497171 is fixed
            self.assertEqual(metric[field], metric_from_list[field], field)

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

    def test_metric_by_name_scenario(self):
        # PREPARE REQUIREMENT
        self.gnocchi("archive-policy", params="create metric-test2 "
                     "--back-window 0 -d granularity:1s,points:86400")
        self.gnocchi("resource", params="create generic -a id:metric-res")

        # CREATE
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test2 -r metric-res metric-name")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual(self.clients.project_id,
                         metric["created_by_project_id"])
        self.assertEqual(self.clients.user_id, metric["created_by_user_id"])
        self.assertEqual('metric-name', metric["name"])
        self.assertNotEqual('None', metric["resource"])
        self.assertIn("metric-test", metric["archive_policy/name"])

        # GET
        result = self.gnocchi('metric', params="show metric-name metric-res")
        metric_get = self.details_multiple(result)[0]
        self.assertEqual(metric, metric_get)

        # MEASURES ADD
        result = self.gnocchi('measures',
                              params=("add metric-name metric-res "
                                      "-m '2015-03-06T14:33:57@43.11' "
                                      "--measure '2015-03-06T14:34:12@12'"))
        self.assertEqual("", result)

        # MEASURES GET
        result = self.retry_gnocchi(
            5, 'measures', params=("get metric-name metric-res "
                                   "--aggregation mean "
                                   "--start 2015-03-06T14:32:00 "
                                   "--end 2015-03-06T14:36:00"))

        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES AGGREGATION
        result = self.gnocchi(
            'measures', params=("--debug aggregation "
                                "--query \"id='metric-res'\" "
                                "-m metric-name "
                                "--aggregation mean "
                                "--needed-overlap 0 "
                                "--start 2015-03-06T14:32:00 "
                                "--end 2015-03-06T14:36:00"))
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # LIST
        result = self.gnocchi('metric', params="list")
        metrics = self.parser.listing(result)
        metric_from_list = [p for p in metrics
                            if p['archive_policy/name'] == 'metric-test2'][0]
        for field in ["archive_policy/name", "name"]:
            # FIXME(sileht): add "resource_id" or "resource"
            # when LP#1497171 is fixed
            self.assertEqual(metric[field], metric_from_list[field])

        # DELETE
        result = self.gnocchi('metric', params="delete metric-name metric-res")
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('metric', params="show metric-name metric-res",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('metric', params="delete metric-name metric-res",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Not Found (HTTP 404)")
