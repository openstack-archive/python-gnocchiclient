# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

from keystoneclient import session as keystoneclient_session

from gnocchiclient.v1 import archivepolicy
from gnocchiclient.v1 import resource


class Client(object):
    """Client for the Gnocchi v1 API.

    :param string auth: An optional keystoneclient authentication plugin
                        to authenticate the session with
    :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`
    :param endpoint: The optional Gnocchi API endpoint
    :type endpoint: str
    :param interface: The endpoint interface ('public', 'internal', 'admin')
    :type interface: str
    :param region_name: The keystone region name
    :type region_name: str
    :param \*\*kwargs: Any option supported by
                      :py:class:`keystoneclient.session.Session`

    """

    _VERSION = "v1"

    def __init__(self, auth=None, endpoint=None, interface=None,
                 region_name=None, **kwargs):
        """Initialize a new client for the Gnocchi v1 API."""
        self.api = keystoneclient_session.Session(auth, **kwargs)
        self.resource = resource.ResourceManager(self)
        self.archivepolicy = archivepolicy.ArchivePolicyManager(self)
        self.interface = interface
        self.region_name = region_name
        self._endpoint = endpoint

    @property
    def endpoint(self):
        if self._endpoint is None:
            self._endpoint = self.api.get_endpoint(
                service_type='metric', interface=self.interface,
                region_name=self.region_name)
        return self._endpoint

    def _build_url(self, url_suffix):
        return "%s/%s/%s" % (self.endpoint.rstrip("/"),
                             self._VERSION,
                             url_suffix)
