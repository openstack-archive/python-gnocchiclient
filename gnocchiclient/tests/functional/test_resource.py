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
from gnocchiclient import utils


class ResourceClientTest(base.ClientTestBase):
    RESOURCE_ID = str(uuid.uuid4())
    RAW_RESOURCE_ID2 = str(uuid.uuid4()) + "/foo"
    RESOURCE_ID2 = utils.encode_resource_id(RAW_RESOURCE_ID2)
    PROJECT_ID = str(uuid.uuid4())

    def test_help(self):
        self.gnocchi("help", params="resource list")
        self.gnocchi("help", params="resource history")
        self.gnocchi("help", params="resource search")

    def test_resource_scenario(self):
        apname = str(uuid.uuid4())
        # Create an archive policy
        self.gnocchi(
            u'archive-policy', params=u"create %s"
            u" -d granularity:1s,points:86400" % apname)

        # CREATE
        result = self.gnocchi(
            u'resource', params=u"create %s --type generic" %
            self.RESOURCE_ID)
        resource = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource["id"])
        self.assertEqual('None', resource["project_id"])
        self.assertNotEqual('None', resource["started_at"])

        # CREATE FAIL
        result = self.gnocchi('resource',
                              params="create generic -a id:%s" %
                              self.RESOURCE_ID,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource %s already exists (HTTP 409)" % self.RESOURCE_ID)

        # UPDATE
        result = self.gnocchi(
            'resource', params=("update -t generic %s -a project_id:%s "
                                "-n temperature:%s" %
                                (self.RESOURCE_ID, self.PROJECT_ID, apname)))
        resource_updated = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource_updated["id"])
        self.assertEqual(self.PROJECT_ID, resource_updated["project_id"])
        self.assertEqual(resource["started_at"],
                         resource_updated["started_at"])
        self.assertIn("temperature", resource_updated["metrics"])

        # GET
        result = self.gnocchi(
            'resource', params="show -t generic %s" % self.RESOURCE_ID)
        resource_got = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource_got["id"])
        self.assertEqual(self.PROJECT_ID, resource_got["project_id"])
        self.assertEqual(resource["started_at"], resource_got["started_at"])
        self.assertIn("temperature", resource_got["metrics"])

        # HISTORY
        result = self.gnocchi(
            'resource', params="history --type generic %s" % self.RESOURCE_ID)
        resource_history = self.parser.listing(result)
        self.assertEqual(2, len(resource_history))
        self.assertEqual(self.RESOURCE_ID, resource_history[0]["id"])
        self.assertEqual(self.RESOURCE_ID, resource_history[1]["id"])
        self.assertEqual("None", resource_history[0]["project_id"])
        self.assertEqual(self.PROJECT_ID, resource_history[1]["project_id"])

        # LIST
        result = self.gnocchi('resource', params="list -t generic")
        self.assertIn(self.RESOURCE_ID,
                      [r['id'] for r in self.parser.listing(result)])
        resource_list = [r for r in self.parser.listing(result)
                         if r['id'] == self.RESOURCE_ID][0]
        self.assertEqual(self.RESOURCE_ID, resource_list["id"])
        self.assertEqual(self.PROJECT_ID, resource_list["project_id"])
        self.assertEqual(resource["started_at"], resource_list["started_at"])

        # Search
        result = self.gnocchi('resource',
                              params=("search --type generic "
                                      "'project_id=%s'"
                                      ) % self.PROJECT_ID)
        resource_list = self.parser.listing(result)[0]
        self.assertEqual(self.RESOURCE_ID, resource_list["id"])
        self.assertEqual(self.PROJECT_ID, resource_list["project_id"])
        self.assertEqual(resource["started_at"], resource_list["started_at"])

        # UPDATE with Delete metric
        result = self.gnocchi(
            'resource', params=("update -t generic %s -a project_id:%s "
                                "-d temperature" %
                                (self.RESOURCE_ID, self.PROJECT_ID)))
        resource_updated = self.details_multiple(result)[0]
        self.assertNotIn("temperature", resource_updated["metrics"])

        result = self.gnocchi(
            'resource', params=("update %s -d temperature" % self.RESOURCE_ID),
            fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Metric name temperature not found")

        # CREATE 2
        result = self.gnocchi(
            'resource', params=("create %s -t generic "
                                "-a project_id:%s"
                                ) % (self.RAW_RESOURCE_ID2, self.PROJECT_ID))
        resource2 = self.details_multiple(result)[0]
        self.assertEqual(self.RESOURCE_ID2, resource2["id"])
        self.assertEqual(self.RAW_RESOURCE_ID2,
                         resource2["original_resource_id"])
        self.assertEqual(self.PROJECT_ID, resource2["project_id"])
        self.assertNotEqual('None', resource2["started_at"])

        # Search + limit + short
        result = self.gnocchi('resource',
                              params=("search "
                                      "-t generic "
                                      "'project_id=%s' "
                                      "--sort started_at:asc "
                                      "--marker %s "
                                      "--limit 1"
                                      ) % (self.PROJECT_ID, self.RESOURCE_ID))
        resource_limit = self.parser.listing(result)[0]
        self.assertEqual(self.RESOURCE_ID2, resource_limit["id"])
        self.assertEqual(self.PROJECT_ID, resource_limit["project_id"])
        self.assertEqual(resource2["started_at"], resource_limit["started_at"])

        # DELETE
        result = self.gnocchi('resource',
                              params="delete %s" % self.RESOURCE_ID)
        self.assertEqual("", result)
        result = self.gnocchi('resource',
                              params="delete %s" % self.RESOURCE_ID2)
        self.assertEqual("", result)

        # GET FAIL
        result = self.gnocchi('resource',
                              params="show --type generic %s" %
                              self.RESOURCE_ID,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource %s does not exist (HTTP 404)" % self.RESOURCE_ID)

        # DELETE FAIL
        result = self.gnocchi('resource',
                              params="delete %s" % self.RESOURCE_ID,
                              fail_ok=True, merge_stderr=True)
        self.assertFirstLineStartsWith(
            result.split('\n'),
            "Resource %s does not exist (HTTP 404)" % self.RESOURCE_ID)

        # LIST EMPTY
        result = self.gnocchi('resource', params="list -t generic")
        resource_ids = [r['id'] for r in self.parser.listing(result)]
        self.assertNotIn(self.RESOURCE_ID, resource_ids)
        self.assertNotIn(self.RESOURCE_ID2, resource_ids)

        # LIST THE RESOURCES TYPES
        result = self.gnocchi(
            'resource', params="list-types")
        r = self.parser.listing(result)
        self.assertIn({
            'resource_controller_url':
            'http://localhost:8041/v1/resource/generic',
            'resource_type': 'generic'
        }, r)
