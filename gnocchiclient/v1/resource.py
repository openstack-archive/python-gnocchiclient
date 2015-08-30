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


class ResourceManager(base.Manager):
    def list(self, resource_type="generic", details=False, history=False):
        """List resources

        :param resource_type: Type of the resource
        :type resource_type: str
        :param details: Show all attributes of resources
        :type details: bool
        :param history: Show the history of resources
        :type history: bool
        """
        details = "true" if details else "false"
        history = "true" if history else "false"
        url = self.client._build_url("resource/%s?details=%s&history=%s" % (
            resource_type, details, history))
        return self.client.api.get(url).json()

    def get(self, resource_type, resource_id):
        """Get a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource_id: ID of the resource
        :type resource_id: str
        """
        url = self.client._build_url("resource/%s/%s" % (
            resource_type, resource_id))
        return self.client.api.get(url).json()

    def create(self, resource_type, resource):
        """Create a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource: Attribute of the resource
        :type resource: dict
        """
        url = self.client._build_url("resource/%s" % resource_type)
        return self.client.api.post(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(resource)).json()

    def update(self, resource_type, resource_id, resource):
        """Update a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource_id: ID of the resource
        :type resource_id: str
        :param resource: Attribute of the resource
        :type resource: dict
        """

        url = self.client._build_url("resource/%s/%s" % (resource_type,
                                                         resource_id))
        return self.client.api.patch(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(resource)).json()

    def delete(self, resource_id):
        """Delete a resource

        :param resource_id: ID of the resource
        :type resource_id: str
        """
        url = self.client._build_url("resource/generic/%s" % (resource_id))
        self.client.api.delete(url)

    def search(self, resource_type="generic", request=None, details=False,
               history=False):
        """List resources

        :param resource_type: Type of the resource
        :param resource_type: str
        :param request: The search request dictionary
        :type resource_type: dict
        :param details: Show all attributes of resources
        :type details: bool
        :param history: Show the history of resources
        :type history: bool

        See Gnocchi REST API documentation for the format
        of *request dictionary*
        http://docs.openstack.org/developer/gnocchi/rest.html#searching-for-resources
        """

        request = request or {}
        details = "true" if details else "false"
        history = "true" if history else "false"
        url = self.client._build_url(
            "/search/resource/%s?details=%s&history=%s" % (
                resource_type, details, history))
        return self.client.api.post(
            url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(request)).json()
