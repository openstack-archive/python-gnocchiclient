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
from six.moves.urllib import parse as urllib_parse

from gnocchiclient.v1 import base


def _get_pagination_options(details=False, history=False,
                            limit=None, marker=None, sorts=None):
    options = []
    if details:
        options.append("details=true")
    if history:
        options.append("history=true")
    if limit:
        options.append("limit=%d" % limit)
    if marker:
        options.append("marker=%s" % urllib_parse.quote(marker))
    for sort in sorts or []:
        options.append("sort=%s" % urllib_parse.quote(sort))
    if options:
        return "?%s" % "&".join(options)
    else:
        return ""


class ResourceManager(base.Manager):
    url = "v1/resource/"

    DEFAULT_HEADERS = {"Accept": "application/json, */*"}

    def list(self, resource_type="generic", details=False, history=False,
             limit=None, marker=None, sorts=None):
        """List resources

        :param resource_type: Type of the resource
        :type resource_type: str
        :param details: Show all attributes of resources
        :type details: bool
        :param history: Show the history of resources
        :type history: bool
        :param limit: maximum number of resources to return
        :type limit: int
        :param marker: the last item of the previous page; we returns the next
                       results after this value.
        :param sorts: list of resource attributes to order by. (example
                      ["user_id:desc-nullslast", "project_id:asc"]
        :type sorts: list of str
        """
        qs = _get_pagination_options(details, history, limit, marker, sorts)
        return self.client.api.get(self.url + resource_type + qs,
                                   headers=self.DEFAULT_HEADERS).json()

    def get(self, resource_type, resource_id, history=False):
        """Get a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource_id: ID of the resource
        :type resource_id: str
        :param history: Show the history of the resource
        :type history: bool
        """
        history = "/history" if history else ""
        url = self.url + "%s/%s%s" % (resource_type, resource_id, history)
        return self.client.api.get(url,
                                   headers=self.DEFAULT_HEADERS).json()

    def history(self, resource_type, resource_id, details=False,
                limit=None, marker=None, sorts=None):
        """Get a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource_id: ID of the resource
        :type resource_id: str
        :param details: Show all attributes of resources
        :type details: bool
        :param limit: maximum number of resources to return
        :type limit: int
        :param marker: the last item of the previous page; we returns the next
                       results after this value.
        :param sorts: list of resource attributes to order by. (example
                      ["user_id:desc-nullslast", "project_id:asc"]
        :type sorts: list of str
        """
        qs = _get_pagination_options(details, False, limit, marker, sorts)
        url = "%s%s/%s/history?%s" % (self.url, resource_type, resource_id, qs)
        return self.client.api.get(url).json()

    def create(self, resource_type, resource):
        """Create a resource

        :param resource_type: Type of the resource
        :type resource_type: str
        :param resource: Attribute of the resource
        :type resource: dict
        """
        headers = {'Content-Type': "application/json"}
        headers.update(self.DEFAULT_HEADERS)
        return self.client.api.post(
            self.url + resource_type,
            headers=headers,
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
        headers = {'Content-Type': "application/json"}
        headers.update(self.DEFAULT_HEADERS)
        return self.client.api.patch(
            self.url + resource_type + "/" + resource_id,
            headers=headers,
            data=jsonutils.dumps(resource)).json()

    def delete(self, resource_id):
        """Delete a resource

        :param resource_id: ID of the resource
        :type resource_id: str
        """
        self.client.api.delete(self.url + "generic/" + resource_id,
                               headers=self.DEFAULT_HEADERS)

    def search(self, resource_type="generic", query=None, details=False,
               history=False, limit=None, marker=None, sorts=None):
        """List resources

        :param resource_type: Type of the resource
        :param resource_type: str
        :param query: The query dictionary
        :type query: dict
        :param details: Show all attributes of resources
        :type details: bool
        :param history: Show the history of resources
        :type history: bool
        :param limit: maximum number of resources to return
        :type limit: int
        :param marker: the last item of the previous page; we returns the next
                       results after this value.
        :param sorts: list of resource attributes to order by. (example
                      ["user_id:desc-nullslast", "project_id:asc"]
        :type sorts: list of str

        See Gnocchi REST API documentation for the format
        of *query dictionary*
        http://docs.openstack.org/developer/gnocchi/rest.html#searching-for-resources
        """
        headers = {'Content-Type': "application/json"}
        headers.update(self.DEFAULT_HEADERS)
        query = query or {}
        qs = _get_pagination_options(details, False, limit, marker, sorts)
        url = "v1/search/resource/%s?%s" % (resource_type, qs)
        return self.client.api.post(
            url, headers=headers,
            data=jsonutils.dumps(query)).json()
