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
import json
import os
import tempfile

from oslo_utils import uuidutils

from gnocchiclient.tests.functional import base


class MetricClientTest(base.ClientTestBase):
    def test_delete_several_metrics(self):
        apname = uuidutils.generate_uuid()
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create %s "
                     "--back-window 0 -d granularity:1s,points:86400" % apname)
        # Create 2 metrics
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name %s" % apname)
        metric1 = self.details_multiple(result)[0]

        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name %s" % apname)
        metric2 = self.details_multiple(result)[0]

        # DELETE
        result = self.gnocchi('metric', params="delete %s %s"
                              % (metric1["id"], metric2["id"]))
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('metric', params="show %s" % metric1["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Metric %s does not exist (HTTP 404)" %
                                       metric1["id"])
        result = self.gnocchi('metric', params="show %s" % metric2["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(result.split('\n'),
                                       "Metric %s does not exist (HTTP 404)" %
                                       metric2["id"])

    def test_metric_scenario(self):
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create metric-test "
                     "--back-window 0 -d granularity:1s,points:86400")

        # CREATE WITH NAME AND WITHOUT UNIT
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test some-name")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual("admin", metric["creator"])
        self.assertEqual("", metric["created_by_project_id"])
        self.assertEqual("admin", metric["created_by_user_id"])
        self.assertEqual('some-name', metric["name"])
        self.assertEqual('None', metric["unit"])
        self.assertEqual('None', metric["resource/id"])
        self.assertIn("metric-test", metric["archive_policy/name"])

        # CREATE WITH UNIT
        result = self.gnocchi(
            u'metric', params=u"create another-name"
            u" --archive-policy-name metric-test"
            u" --unit some-unit")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual("admin", metric["creator"])
        self.assertEqual("", metric["created_by_project_id"])
        self.assertEqual("admin", metric["created_by_user_id"])
        self.assertEqual('another-name', metric["name"])
        self.assertEqual('some-unit', metric["unit"])
        self.assertEqual('None', metric["resource/id"])
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

        # MEASURES GET with refresh
        result = self.gnocchi('measures',
                              params=("show %s "
                                      "--aggregation mean "
                                      "--granularity 1 "
                                      "--start 2015-03-06T14:32:00 "
                                      "--stop 2015-03-06T14:36:00 "
                                      "--refresh") % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES GET
        result = self.retry_gnocchi(
            5, 'measures', params=("show %s "
                                   "--aggregation mean "
                                   "--granularity 1 "
                                   "--start 2015-03-06T14:32:00 "
                                   "--stop 2015-03-06T14:36:00"
                                   ) % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES GET RESAMPLE
        result = self.retry_gnocchi(
            5, 'measures', params=("show %s "
                                   "--aggregation mean "
                                   "--granularity 1 --resample 3600 "
                                   "--start 2015-03-06T14:32:00 "
                                   "--stop 2015-03-06T14:36:00"
                                   ) % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '3600.0',
                           'timestamp': '2015-03-06T14:00:00+00:00',
                           'value': '27.555'}], measures)

        # MEASURES AGGREGATION
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--metric %s "
                                "--aggregation mean "
                                "--reaggregation sum "
                                "--granularity 1 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00"
                                ) % metric["id"])
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # BATCHING
        measures = json.dumps({
            metric['id']: [{'timestamp': '2015-03-06T14:34:12',
                            'value': 12}]})
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, tmpfile.name)
        with tmpfile as f:
            f.write(measures.encode('utf8'))
        self.gnocchi('measures', params=("batch-metrics %s" % tmpfile.name))
        self.gnocchi('measures', params="batch-metrics -",
                     input=measures.encode('utf8'))

        # LIST
        result = self.gnocchi('metric', params="list")
        metrics = self.parser.listing(result)
        metric_from_list = [p for p in metrics
                            if p['id'] == metric['id']][0]
        for field in ["id", "archive_policy/name", "name"]:
            # FIXME(sileht): add "resource_id" or "resource"
            # when LP#1497171 is fixed
            self.assertEqual(metric[field], metric_from_list[field], field)

        # LIST + limit
        result = self.gnocchi('metric',
                              params=("list "
                                      "--sort name:asc "
                                      "--marker %s "
                                      "--limit 1") % metric['id'])
        metrics = self.parser.listing(result)
        metric_from_list = metrics[0]
        self.assertEqual(1, len(metrics))
        self.assertTrue(metric['name'] < metric_from_list['name'])

        # DELETE
        result = self.gnocchi('metric', params="delete %s" % metric["id"])
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('metric', params="show %s" % metric["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Metric %s does not exist (HTTP 404)" % metric["id"])

        # DELETE FAIL
        result = self.gnocchi('metric', params="delete %s" % metric["id"],
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Metric %s does not exist (HTTP 404)" % metric["id"])

    def test_metric_by_name_scenario(self):
        # PREPARE REQUIREMENT
        self.gnocchi("archive-policy", params="create metric-test2 "
                     "--back-window 0 -d granularity:1s,points:86400")
        self.gnocchi("resource", params="create metric-res")

        # CREATE
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test2 -r metric-res metric-name"
            u" --unit some-unit")
        metric = self.details_multiple(result)[0]
        self.assertIsNotNone(metric["id"])
        self.assertEqual("", metric['created_by_project_id'])
        self.assertEqual("admin", metric['created_by_user_id'])
        self.assertEqual("admin", metric['creator'])
        self.assertEqual('metric-name', metric["name"])
        self.assertEqual('some-unit', metric["unit"])
        self.assertNotEqual('None', metric["resource/id"])
        self.assertIn("metric-test", metric["archive_policy/name"])

        # CREATE FAIL
        result = self.gnocchi(
            u'metric', params=u"create"
            u" --archive-policy-name metric-test2 -r metric-res metric-name",
            fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Named metric metric-name already exists (HTTP 409)")

        # GET
        result = self.gnocchi('metric',
                              params="show -r metric-res metric-name")
        metric_get = self.details_multiple(result)[0]
        self.assertEqual(metric, metric_get)

        # MEASURES ADD
        result = self.gnocchi('measures',
                              params=("add metric-name -r metric-res "
                                      "-m '2015-03-06T14:33:57@43.11' "
                                      "--measure '2015-03-06T14:34:12@12'"))
        self.assertEqual("", result)

        # MEASURES AGGREGATION with refresh
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--query \"id='metric-res'\" "
                                "--resource-type \"generic\" "
                                "-m metric-name "
                                "--aggregation mean "
                                "--needed-overlap 0 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00 "
                                "--refresh"))
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
                                "--query \"id='metric-res'\" "
                                "--resource-type \"generic\" "
                                "-m metric-name "
                                "--aggregation mean "
                                "--needed-overlap 0 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00"))
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES AGGREGATION WITH FILL
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--query \"id='metric-res'\" "
                                "--resource-type \"generic\" "
                                "-m metric-name --fill 0 "
                                "--granularity 1 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00"))
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES AGGREGATION RESAMPLE
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--query \"id='metric-res'\" "
                                "--resource-type \"generic\" "
                                "-m metric-name --granularity 1 "
                                "--aggregation mean --resample=3600 "
                                "--needed-overlap 0 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00"))
        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '3600.0',
                           'timestamp': '2015-03-06T14:00:00+00:00',
                           'value': '27.555'}], measures)

        # MEASURES AGGREGATION GROUPBY
        result = self.gnocchi(
            'measures', params=("aggregation "
                                "--groupby project_id "
                                "--groupby user_id "
                                "--query \"id='metric-res'\" "
                                "--resource-type \"generic\" "
                                "-m metric-name "
                                "--aggregation mean "
                                "--needed-overlap 0 "
                                "--start 2015-03-06T14:32:00 "
                                "--stop 2015-03-06T14:36:00"))
        measures = self.parser.listing(result)
        self.assertEqual([{'group': 'project_id: None, user_id: None',
                           'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'group': 'project_id: None, user_id: None',
                           'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # MEASURES GET
        result = self.gnocchi('measures',
                              params=("show metric-name -r metric-res "
                                      "--aggregation mean "
                                      "--start 2015-03-06T14:32:00 "
                                      "--stop 2015-03-06T14:36:00"))

        measures = self.parser.listing(result)
        self.assertEqual([{'granularity': '1.0',
                           'timestamp': '2015-03-06T14:33:57+00:00',
                           'value': '43.11'},
                          {'granularity': '1.0',
                           'timestamp': '2015-03-06T14:34:12+00:00',
                           'value': '12.0'}], measures)

        # BATCHING
        measures = json.dumps({'metric-res': {'metric-name': [{
            'timestamp': '2015-03-06T14:34:12', 'value': 12
        }]}})
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, tmpfile.name)
        with tmpfile as f:
            f.write(measures.encode('utf8'))

        self.gnocchi('measures', params=("batch-resources-metrics %s" %
                                         tmpfile.name))
        self.gnocchi('measures', params="batch-resources-metrics -",
                     input=measures.encode('utf8'))

        # BATCHING --create-metrics
        measures = json.dumps({'metric-res': {'unknown-metric-name': [{
            'timestamp': '2015-03-06T14:34:12', 'value': 12
        }]}})
        self.gnocchi('measures',
                     params="batch-resources-metrics --create-metrics -",
                     input=measures.encode('utf8'),)

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
        result = self.gnocchi('metric',
                              params="delete -r metric-res metric-name")
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('metric',
                              params="show -r metric-res metric-name",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Metric metric-name does not exist (HTTP 404)")

        # DELETE FAIL
        result = self.gnocchi('metric',
                              params="delete -r metric-res metric-name",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Metric metric-name does not exist (HTTP 404)")

        # GET RESOURCE ID
        result = self.gnocchi(
            'resource', params="show -t generic metric-res")
        resource_id = self.details_multiple(result)[0]["id"]

        # DELETE RESOURCE
        result = self.gnocchi('resource', params="delete metric-res")
        self.assertEqual("", result)

        # GET FAIL WITH RESOURCE ERROR
        result = self.gnocchi('metric',
                              params="show metric-name -r metric-res",
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource %s does not exist (HTTP 404)" % resource_id)
