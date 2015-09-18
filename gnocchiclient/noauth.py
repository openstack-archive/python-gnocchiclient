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

from keystoneclient.auth import base
from oslo_config import cfg
import six


class GnocchiNoAuthException(Exception):
    pass


class GnocchiNoAuthPlugin(base.BaseAuthPlugin):
    """No authentication plugin for Gnocchi

    This is a keystoneclient plugin that instead of
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

    @classmethod
    def get_options(cls):
        options = super(GnocchiNoAuthPlugin, cls).get_options()
        options.extend([
            cfg.StrOpt('user-id', help='User ID', required=True),
            cfg.StrOpt('project-id', help='Project ID', required=True),
            cfg.StrOpt('gnocchi-endpoint', help='Gnocchi endpoint',
                       dest="endpoint", required=True),
        ])
        return options

    @classmethod
    def register_argparse_arguments(cls, parser):
        """Register the CLI options provided by a specific plugin.

        Given a plugin class convert it's options into argparse arguments and
        add them to a parser.

        :param parser: the parser to attach argparse options.
        :type parser: argparse.ArgumentParser
        """

        # NOTE(jamielennox): ideally oslo_config would be smart enough to
        # handle all the Opt manipulation that goes on in this file. However it
        # is currently not.  Options are handled in as similar a way as
        # possible to oslo_config such that when available we should be able to
        # transition.

        # NOTE(sileht): We override the keystoneclient one to remove OS prefix
        # and allow to use required parameters
        for opt in cls.get_options():
            args = []
            envs = []

            for o in [opt] + opt.deprecated_opts:
                args.append('--%s' % o.name)
                envs.append('GNOCCHI_%s' % o.name.replace('-', '_').upper())

            # select the first ENV that is not false-y or return None
            env_vars = (os.environ.get(e) for e in envs)
            default = six.next(six.moves.filter(None, env_vars), None)

            parser.add_argument(*args,
                                default=default or opt.default,
                                metavar=opt.metavar,
                                help=opt.help,
                                dest='os_%s' % opt.dest,
                                required=opt.required)
