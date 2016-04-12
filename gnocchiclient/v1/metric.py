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

from gnocchiclient import utils
from gnocchiclient.v1 import base


class MetricManager(base.Manager):
    metric_url = "v1/metric/"
    resource_url = "v1/resource/generic/%s/metric/"
    metric_batch_url = "v1/batch/metrics/measures"
    resources_batch_url = "v1/batch/resources/metrics/measures"

    def list(self):
        """List archive metrics

        """
        return self._get(self.metric_url).json()

    @staticmethod
    def _ensure_metric_is_uuid(metric, attribute="resource_id"):
        try:
            uuid.UUID(metric)
        except ValueError:
            raise TypeError("%s is required to get a metric by name" %
                            attribute)

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
            url = self.metric_url + metric
        else:
            resource_id = utils.encode_resource_id(resource_id)
            url = (self.resource_url % resource_id) + metric
        return self._get(url).json()

    # FIXME(jd): remove refetch_metric when LP#1497171 is fixed
    def create(self, metric, refetch_metric=True):
        """Create an metric

        :param metric: The metric
        :type metric: dict
        """
        resource_id = metric.get('resource_id')

        if resource_id is None:
            metric = self._post(
                self.metric_url, headers={'Content-Type': "application/json"},
                data=jsonutils.dumps(metric)).json()
            # FIXME(sileht): create and get have a
            # different output: LP#1497171
            if refetch_metric:
                return self.get(metric["id"])
            return metric

        metric_name = metric.get('name')

        if metric_name is None:
            raise TypeError("metric_name is required if resource_id is set")

        del metric['resource_id']
        resource_id = utils.encode_resource_id(resource_id)
        metric = {metric_name: metric}
        metric = self._post(
            self.resource_url % resource_id,
            headers={'Content-Type': "application/json"},
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
            url = self.metric_url + metric
        else:
            resource_id = utils.encode_resource_id(resource_id)
            url = self.resource_url % resource_id + metric
        self._delete(url)

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
            url = self.metric_url + metric + "/measures"
        else:
            resource_id = utils.encode_resource_id(resource_id)
            url = self.resource_url % resource_id + metric + "/measures"
        return self._post(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(measures))

    def batch_metrics_measures(self, measures):
        """Add measurements to metrics

        :param measures: measurements
        :type dict(metric_id: list of dict(timestamp=timestamp, value=float))
        """

        return self._post(
            self.metric_batch_url,
            headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(measures))

    def batch_resources_metrics_measures(self, measures):
        """Add measurements to named metrics if resources

        :param measures: measurements
        :type dict(resource_id: dict(metric_name:
            list of dict(timestamp=timestamp, value=float)))
        """

        return self._post(
            self.resources_batch_url,
            headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(measures))

    def get_measures(self, metric, start=None, stop=None, aggregation=None,
                     granularity=None, resource_id=None, **kwargs):
        """Get measurements of a metric

        :param metric: ID or Name of the metric
        :type metric: str
        :param start: beginning of the period
        :type start: timestamp
        :param stop: end of the period
        :type stop: timestamp
        :param aggregation: aggregation to retrieve
        :type aggregation: str
        :param granularity: granularity to retrieve (in seconds)
        :type granularity: int
        :param resource_id: ID of the resource (required
                            to get a metric by name)
        :type resource_id: str

        All other arguments are arguments are dedicated to custom aggregation
        method passed as-is to the Gnocchi.
        """

        if isinstance(start, datetime.datetime):
            start = start.isoformat()
        if isinstance(stop, datetime.datetime):
            stop = stop.isoformat()

        params = dict(start=start, stop=stop, aggregation=aggregation,
                      granularity=granularity)
        params.update(kwargs)
        if resource_id is None:
            self._ensure_metric_is_uuid(metric)
            url = self.metric_url + metric + "/measures"
        else:
            resource_id = utils.encode_resource_id(resource_id)
            url = self.resource_url % resource_id + metric + "/measures"
        return self._get(url, params=params).json()

    def aggregation(self, metrics, query=None,
                    start=None, stop=None, aggregation=None,
                    needed_overlap=None, resource_type="generic",
                    groupby=None):
        """Get measurements of a aggregated metrics

        :param metrics: IDs of metric or metric name
        :type metric: list or str
        :param query: The query dictionary
        :type query: dict
        :param start: beginning of the period
        :type start: timestamp
        :param stop: end of the period
        :type stop: timestamp
        :param aggregation: aggregation to retrieve
        :type aggregation: str
        :param resource_type: type of resource for the query
        :type resource_type: str
        :param groupby: list of attribute to group by
        :type groupby: list

        See Gnocchi REST API documentation for the format
        of *query dictionary*
        http://docs.openstack.org/developer/gnocchi/rest.html#searching-for-resources
        """

        if isinstance(start, datetime.datetime):
            start = start.isoformat()
        if isinstance(stop, datetime.datetime):
            stop = stop.isoformat()

        params = dict(start=start, stop=stop, aggregation=aggregation,
                      needed_overlap=needed_overlap,
                      groupby=groupby)
        if query is None:
            for metric in metrics:
                self._ensure_metric_is_uuid(metric)
            params['metric'] = metrics
            return self._get("v1/aggregation/metric",
                             params=params).json()
        else:
            return self._post(
                "v1/aggregation/resource/%s/metric/%s?%s" % (
                    resource_type, metrics,
                    utils.dict_to_querystring(params)),
                headers={'Content-Type': "application/json"},
                data=jsonutils.dumps(query)).json()
