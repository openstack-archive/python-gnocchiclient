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

import os

from keystoneauth1 import loading
from keystoneauth1 import plugin


class GnocchiNoAuthPlugin(plugin.BaseAuthPlugin):
    """No authentication plugin for Gnocchi

    This is a keystoneauth plugin that instead of
    doing authentication, it just fill the 'x-user-id'
    and 'x-project-id' headers with the user provided one.
    """
    def __init__(self, user_id, project_id, endpoint):
        self._user_id = user_id
        self._project_id = project_id
        self._endpoint = endpoint

    def get_token(self, session, **kwargs):
        return '<no-token-needed>'

    def get_headers(self, session, **kwargs):
        return {'x-user-id': self._user_id,
                'x-project-id': self._project_id}

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
    @property
    def plugin_class(self):
        return GnocchiNoAuthPlugin

    def get_options(self):
        options = super(GnocchiNoAuthLoader, self).get_options()
        options.extend([
            GnocchiOpt('user-id', help='User ID', required=True),
            GnocchiOpt('project-id', help='Project ID', required=True),
            GnocchiOpt('gnocchi-endpoint', help='Gnocchi endpoint',
                       dest="endpoint", required=True),
        ])
        return options
