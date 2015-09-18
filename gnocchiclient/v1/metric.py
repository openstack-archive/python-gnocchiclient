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

import datetime
import uuid

from oslo_serialization import jsonutils

from gnocchiclient.v1 import base


class MetricManager(base.Manager):

    def list(self):
        """List archive metrics

        """
        url = self.client._build_url("metric")
        return self.client.api.get(url).json()

    @staticmethod
    def _ensure_metric_is_uuid(metric):
        try:
            uuid.UUID(metric)
        except ValueError:
            raise TypeError("resource_id is required to get a metric by name")

    def get(self, metric, resource_id=None):
        """Get an metric

        :param metric: ID or Name of the metric
        :type metric: str
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str
        """
        if resource_id is None:
            self._ensure_metric_is_uuid(metric)
            url = self.client._build_url("metric/%s" % metric)
        else:
            url = self.client._build_url("resource/generic/%s/metric/%s" % (
                resource_id, metric))
        return self.client.api.get(url).json()

    def create(self, metric, resource_id=None, metric_name=None):
        """Create an metric

        :param metric: The metric
        :type metric: str
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str
        """
        if resource_id is None and metric_name is None:
            url = self.client._build_url("metric")
            metric = self.client.api.post(
                url, headers={'Content-Type': "application/json"},
                data=jsonutils.dumps(metric)).json()
            # FIXME(sileht): create and get have a
            # different output: LP#1497171
            return self.get(metric["id"])
        elif ((resource_id is None and metric_name is not None) or
                (resource_id is not None and metric_name is None)):
            raise TypeError("resource_id and metric_name are "
                            "mutually required")
        else:
            url = self.client._build_url("resource/generic/%s/metric" %
                                         resource_id)
            metric = {metric_name: metric}
            metric = self.client.api.post(
                url, headers={'Content-Type': "application/json"},
                data=jsonutils.dumps(metric))
            return self.get(metric_name, resource_id)

    def delete(self, metric, resource_id=None):
        """Delete an metric

        :param metric: ID or Name of the metric
        :type metric: str
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str
        """
        if resource_id is None:
            self._ensure_metric_is_uuid(metric)
            url = self.client._build_url("metric/%s" % metric)
        else:
            url = self.client._build_url("resource/generic/%s/metric/%s" % (
                resource_id, metric))
        self.client.api.delete(url)

    def add_measures(self, metric, measures, resource_id=None):
        """Add measurements to a metric

        :param metric: ID or Name of the metric
        :type metric: str
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str
        :param measures: measurements
        :type measures: list of dict(timestamp=timestamp, value=float)
        """
        if resource_id is None:
            self._ensure_metric_is_uuid(metric)
            url = self.client._build_url("metric/%s/measures" % metric)
        else:
            url = self.client._build_url(
                "resource/generic/%s/metric/%s/measures" % (
                    resource_id, metric))
        return self.client.api.post(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(measures))

    def get_measures(self, metric, start=None, end=None, aggregation=None,
                     resource_id=None, **kwargs):
        """Get measurements of a metric

        :param metric: ID or Name of the metric
        :type metric: str
        :param start: begin of the period
        :type start: timestamp
        :param end: end of the period
        :type end: timestamp
        :param aggregation: aggregation to retrieve
        :type aggregation: str
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str

        All other arguments are arguments are dedicated to custom aggregation
        method passed as-is to the Gnocchi.
        """

        if isinstance(start, datetime.datetime):
            start = start.isoformat()
        if isinstance(end, datetime.datetime):
            end = end.isoformat()

        params = dict(start=start, end=end, aggregation=aggregation)
        params.update(kwargs)
        if resource_id is None:
            self._ensure_metric_is_uuid(metric)
            url = self.client._build_url("metric/%s/measures" % metric)
        else:
            url = self.client._build_url(
                "resource/generic/%s/metric/%s/measures" % (
                    resource_id, metric))
        return self.client.api.get(url, params=params).json()
