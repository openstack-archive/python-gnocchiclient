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

import json

from keystoneclient import session as keystoneclient_session


class Manager(object):
    def __init__(self, client):
        self.client = client


class ResourceManager(Manager):
    def list(self, resource_type="generic", details=False, history=False):
        details = "true" if details else "false"
        history = "true" if history else "false"
        url = self.client.url("resource/%s?details=%s&history=%s" % (
            resource_type, details, history))
        return self.client.api.get(url).json()

    def get(self, resource_type, resource_id):
        url = self.client.url("resource/%s/%s" % (
            resource_type, resource_id))
        return self.client.api.get(url).json()

    def create(self, resource_type, resource):
        url = self.client.url("resource/%s" % resource_type)
        return self.client.api.post(
            url, headers={'Content-Type': "application/json"},
            data=json.dumps(resource)).json()


class Client(object):
    """Client for the Gnocchi v1 API.

    :param string auth: An keystoneclient authentication plugin to
                        authenticate the session with
    :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`
    """

    VERSION = "v1"

    def __init__(self, auth, *args, **kwargs):
        """Initialize a new client for the Gnocchi v1 API."""
        self.api = keystoneclient_session.Session(auth, *args, **kwargs)
        self.resource = ResourceManager(self)
        self._endpoint = None

    @property
    def endpoint(self):
        if self._endpoint is None:
            self._endpoint = self.api.get_endpoint(service_type='metric')
        return self._endpoint

    def url(self, url_suffix):
        return "%s/%s/%s" % (self.endpoint.rstrip("/"),
                             self.VERSION,
                             url_suffix)
