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


class ResourceTypeManager(base.Manager):
    url = "v1/resource_type/"

    def list(self):
        """List resource types."""
        return self._get(self.url).json()

    def create(self, resource_type):
        """Create a resource type

        :param resource_type: resource type
        :type resource_type: dict
        """
        return self._post(
            self.url,
            headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(resource_type)).json()

    def get(self, name):
        """Get a resource type

        :param name: name of the resource type
        :type name: str
        """
        return self._get(self.url + name,
                         headers={'Content-Type': "application/json"}).json()

    def delete(self, name):
        """Delete a resource type

        :param resource_type: Resource type
        :type resource_type: dict
        """
        self._delete(self.url + name)
