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


class ArchivePolicyManager(base.Manager):

    url = "v1/archive_policy/"

    def list(self):
        """List archive policies

        """
        return self._get(self.url).json()

    def get(self, name):
        """Get an archive policy

        :param name: Name of the archive policy
        :type name: str
        """
        return self._get(self.url + name).json()

    def create(self, archive_policy):
        """Create an archive policy

        :param archive_policy: the archive policy
        :type archive_policy: dict

        """
        return self._post(
            self.url, headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(archive_policy)).json()

    def update(self, name, archive_policy):
        """Update an archive policy

        :param name: the name of archive policy
        :type name: str
        :param archive_policy: the archive policy
        :type archive_policy: dict

        """
        return self._patch(
            self.url + '/' + name,
            headers={'Content-Type': "application/json"},
            data=jsonutils.dumps(archive_policy)).json()

    def delete(self, name):
        """Delete an archive policy

        :param name: Name of the archive policy
        :type name: str
        """
        self._delete(self.url + name)
