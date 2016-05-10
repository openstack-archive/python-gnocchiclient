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


class BenchmarkMetricTest(base.ClientTestBase):
    def test_benchmark_metric_create_wrong_workers(self):
        result = self.gnocchi(
            u'benchmark', params=u"metric create -n 0",
            fail_ok=True, merge_stderr=True)
        self.assertIn("0 must be greater than 0", result)

    def test_benchmark_metric_create(self):
        apname = str(uuid.uuid4())
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create %s "
                     "--back-window 0 -d granularity:1s,points:86400" % apname)

        result = self.gnocchi(
            u'benchmark', params=u"metric create -n 10 -a %s" % apname)
        result = self.details_multiple(result)[0]
        self.assertEqual(10, int(result['create executed']))
        self.assertLessEqual(int(result['create failures']), 10)
        self.assertLessEqual(int(result['delete executed']),
                             int(result['create executed']))

        result = self.gnocchi(
            u'benchmark', params=u"metric create -k -n 10 -a %s" % apname)
        result = self.details_multiple(result)[0]
        self.assertEqual(10, int(result['create executed']))
        self.assertLessEqual(int(result['create failures']), 10)
        self.assertNotIn('delete executed', result)

    def test_benchmark_metric_get(self):
        apname = str(uuid.uuid4())
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create %s "
                     "--back-window 0 -d granularity:1s,points:86400" % apname)

        result = self.gnocchi(
            u'metric', params=u"create -a %s" % apname)
        metric = self.details_multiple(result)[0]

        result = self.gnocchi(
            u'benchmark', params=u"metric show -n 10 %s" % metric['id'])
        result = self.details_multiple(result)[0]
        self.assertEqual(10, int(result['show executed']))
        self.assertLessEqual(int(result['show failures']), 10)

    def test_benchmark_measures_add(self):
        apname = str(uuid.uuid4())
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create %s "
                     "--back-window 0 -d granularity:1s,points:86400" % apname)

        result = self.gnocchi(
            u'metric', params=u"create -a %s" % apname)
        metric = self.details_multiple(result)[0]

        result = self.gnocchi(
            u'benchmark', params=u"measures add -n 10 -b 4 %s" % metric['id'])
        result = self.details_multiple(result)[0]
        self.assertEqual(2, int(result['push executed']))
        self.assertLessEqual(int(result['push failures']), 2)

        result = self.gnocchi(
            u'benchmark',
            params=u"measures add -s 2010-01-01 -n 10 -b 4 %s"
            % metric['id'])
        result = self.details_multiple(result)[0]
        self.assertEqual(2, int(result['push executed']))
        self.assertLessEqual(int(result['push failures']), 2)

        result = self.gnocchi(
            u'benchmark',
            params=u"measures add --wait -s 2010-01-01 -n 10 -b 4 %s"
            % metric['id'])
        result = self.details_multiple(result)[0]
        self.assertEqual(2, int(result['push executed']))
        self.assertLessEqual(int(result['push failures']), 2)
        self.assertIn("extra wait to process measures", result)

    def test_benchmark_measures_show(self):
        apname = str(uuid.uuid4())
        # PREPARE AN ARCHIVE POLICY
        self.gnocchi("archive-policy", params="create %s "
                     "--back-window 0 -d granularity:1s,points:86400" % apname)

        result = self.gnocchi(
            u'metric', params=u"create -a %s" % apname)
        metric = self.details_multiple(result)[0]

        result = self.gnocchi(
            u'benchmark',
            params=u"measures show -n 2 %s"
            % metric['id'])
        result = self.details_multiple(result)[0]
        self.assertEqual(2, int(result['show executed']))
        self.assertLessEqual(int(result['show failures']), 2)
