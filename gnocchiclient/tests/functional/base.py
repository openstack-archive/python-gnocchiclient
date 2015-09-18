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
import shlex
import six
import subprocess
import time
import uuid

from tempest_lib.cli import base
from tempest_lib import exceptions


class GnocchiClient(object):
    """Gnocchi Client for tempest-lib

    This client doesn't use any authentification system
    """

    def __init__(self):
        self.cli_dir = os.environ.get('GNOCCHI_CLIENT_EXEC_DIR')
        self.endpoint = os.environ.get('GNOCCHI_ENDPOINT')
        self.user_id = str(uuid.uuid4())
        self.project_id = str(uuid.uuid4())

    def gnocchi(self, action, flags='', params='',
                fail_ok=False, merge_stderr=False):
        creds = ("--os-auth-plugin gnocchi-noauth "
                 "--user-id %s --project-id %s "
                 "--gnocchi-endpoint %s") % (self.user_id,
                                             self.project_id,
                                             self.endpoint)

        flags = creds + ' ' + flags

        # FIXME(sileht): base.execute is broken in py3 in tempest-lib
        # see: https://review.openstack.org/#/c/218870/
        # return base.execute("gnocchi", action, flags, params, fail_ok,
        #                      merge_stderr, self.cli_dir)

        cmd = "gnocchi"

        # from fixed tempestlib
        cmd = ' '.join([os.path.join(self.cli_dir, cmd),
                        flags, action, params])
        if six.PY2:
            cmd = cmd.encode('utf-8')
        cmd = shlex.split(cmd)
        result = ''
        result_err = ''
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT if merge_stderr else subprocess.PIPE
        proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        result, result_err = proc.communicate()
        if not fail_ok and proc.returncode != 0:
            raise exceptions.CommandFailed(proc.returncode,
                                           cmd,
                                           result,
                                           result_err)
        if six.PY2:
            return result
        else:
            return os.fsdecode(result)


class ClientTestBase(base.ClientTestBase):
    """Base class for gnocchiclient tests.

    Establishes the gnocchi client and retrieves the essential environment
    information.
    """

    def _get_clients(self):
        return GnocchiClient()

    def retry_gnocchi(self, retry, *args, **kwargs):
        result = ""
        while not result.strip() and retry > 0:
            result = self.gnocchi(*args, **kwargs)
            if not result:
                time.sleep(1)
                retry -= 1
        return result

    def gnocchi(self, *args, **kwargs):
        return self.clients.gnocchi(*args, **kwargs)

    def details_multiple(self, output_lines, with_label=False):
        """Return list of dicts with item details from cli output tables.

        If with_label is True, key '__label' is added to each items dict.
        For more about 'label' see OutputParser.tables().

        NOTE(sileht): come from tempest-lib just because cliff use
        Field instead of Property as first columun header.
        """
        items = []
        tables_ = self.parser.tables(output_lines)
        for table_ in tables_:
            if ('Field' not in table_['headers']
                    or 'Value' not in table_['headers']):
                raise exceptions.InvalidStructure()
            item = {}
            for value in table_['values']:
                item[value[0]] = value[1]
            if with_label:
                item['__label'] = table_['label']
            items.append(item)
        return items
