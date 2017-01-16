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

import base64
import os

from keystoneauth1 import loading
from keystoneauth1 import plugin


class GnocchiNoAuthPlugin(plugin.BaseAuthPlugin):
    """No authentication plugin for Gnocchi

    This is a keystoneauth plugin that instead of
    doing authentication, it just fill the 'x-user-id'
    and 'x-project-id' headers with the user provided one.
    """
    def __init__(self, user_id, project_id, roles, endpoint):
        self._user_id = user_id
        self._project_id = project_id
        self._endpoint = endpoint
        self._roles = roles

    def get_headers(self, session, **kwargs):
        return {'x-user-id': self._user_id,
                'x-project-id': self._project_id,
                'x-roles': self._roles}

    def get_user_id(self, session, **kwargs):
        return self._user_id

    def get_project_id(self, session, **kwargs):
        return self._project_id

    def get_endpoint(self, session, **kwargs):
        return self._endpoint


class GnocchiOpt(loading.Opt):
    @property
    def argparse_args(self):
        return ['--%s' % o.name for o in self._all_opts]

    @property
    def argparse_default(self):
        # select the first ENV that is not false-y or return None
        for o in self._all_opts:
            v = os.environ.get('GNOCCHI_%s' % o.name.replace('-', '_').upper())
            if v:
                return v
        return self.default


class GnocchiNoAuthLoader(loading.BaseLoader):
    plugin_class = GnocchiNoAuthPlugin

    def get_options(self):
        options = super(GnocchiNoAuthLoader, self).get_options()
        options.extend([
            GnocchiOpt('user-id', help='User ID', required=True,
                       metavar="<gnocchi user id>"),
            GnocchiOpt('project-id', help='Project ID', required=True,
                       metavar="<gnocchi project id>"),
            GnocchiOpt('roles', help='Roles', default="admin",
                       metavar="<gnocchi roles>"),
            GnocchiOpt('endpoint', help='Gnocchi endpoint',
                       deprecated=[
                           GnocchiOpt('gnocchi-endpoint'),
                       ],
                       dest="endpoint", required=True,
                       metavar="<gnocchi endpoint>"),
        ])
        return options


class GnocchiBasicPlugin(plugin.BaseAuthPlugin):
    """Basic authentication plugin for Gnocchi."""
    def __init__(self, user, endpoint):
        self._user = user.encode('utf-8')
        self._endpoint = endpoint

    def get_headers(self, session, **kwargs):
        return {
            'Authorization':
            (b"basic " + base64.b64encode(
                self._user + b":")).decode('ascii')
        }

    def get_endpoint(self, session, **kwargs):
        return self._endpoint


class GnocchiBasicLoader(loading.BaseLoader):
    plugin_class = GnocchiBasicPlugin

    def get_options(self):
        options = super(GnocchiBasicLoader, self).get_options()
        options.extend([
            GnocchiOpt('user', help='User', required=True,
                       metavar="<gnocchi user>"),
            GnocchiOpt('endpoint', help='Gnocchi endpoint',
                       dest="endpoint", required=True,
                       metavar="<gnocchi endpoint>"),
        ])
        return options
