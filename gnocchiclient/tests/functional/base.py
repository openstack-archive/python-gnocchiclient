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
import uuid

from tempest_lib.cli import base


class GnocchiClient(object):
    """Gnocchi Client for tempest-lib

    This client doesn't use any authentification system
    """

    def __init__(self):
        self.cli_dir = os.environ.get('GNOCCHI_CLIENT_EXEC_DIR')
        self.endpoint = os.environ.get('GNOCCHI_ENDPOINT')
        self.user_id = uuid.uuid4()
        self.project_id = uuid.uuid4()

    def gnocchi(self, action, flags='', params='',
                fail_ok=False, merge_stderr=False):
        creds = ("--os-auth-plugin gnocchi-noauth "
                 "--user-id %s --project-id %s "
                 "--endpoint %s") % (self.user_id,
                                     self.project_id,
                                     self.endpoint)

        flags = creds + ' ' + flags
        return base.execute("gnocchi", action, flags, params, fail_ok,
                            merge_stderr, self.cli_dir)


class ClientTestBase(base.ClientTestBase):
    """Base class for gnocchiclient tests.

    Establishes the gnocchi client and retrieves the essential environment
    information.
    """

    def _get_clients(self):
        return GnocchiClient()

    def gnocchi(self, *args, **kwargs):
        return self.clients.gnocchi(*args, **kwargs)
