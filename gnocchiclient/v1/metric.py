#
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

from oslo_serialization import jsonutils

from gnocchiclient.v1 import base


class MetricManager(base.Manager):

    def list(self):
        """List archive metrics

        """
        url = self.client._build_url("metric")
        return self.client.api.get(url).json()

    def get(self, name):
        """Get an metric

        :param name: Name of the metric
        :type name: str
        """
        url = self.client._build_url("metric/%s" % name)
        return self.client.api.get(url).json()

    def create(self, metric):
        """Create an metric

        :param metric: the metric
        :type metric: dict

        """
        url = self.client._build_url("metric/")
        metric = self.client.api.post(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(metric)).json()
        # FIXME(sileht): create and get have a
        # different output: LP#1497171
        return self.get(metric["id"])

    def delete(self, name):
        """Delete an metric

        :param name: Name of the metric
        :type name: str
        """
        url = self.client._build_url("metric/%s" % name)
        self.client.api.delete(url)
