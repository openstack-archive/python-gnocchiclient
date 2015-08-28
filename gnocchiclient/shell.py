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

import sys

from cliff import app
from cliff import commandmanager
from keystoneclient.auth import cli as keystoneclient_cli

from gnocchiclient import client
from gnocchiclient.version import __version__


class GnocchiShell(app.App):

    def __init__(self, api_version):
        super(GnocchiShell, self).__init__(
            description='Gnocchi command line client',
            # FIXME(sileht): get version from pbr
            version=__version__,
            command_manager=commandmanager.CommandManager(
                'gnocchi.cli.v%s' % api_version),
            deferred_help=True,
            )

        self.api_version = api_version
        self.auth_plugin = None
        self.client = None

    def build_option_parser(self, description, version):
        """Return an argparse option parser for this application.

        Subclasses may override this method to extend
        the parser with more global options.

        :param description: full description of the application
        :paramtype description: str
        :param version: version number for the application
        :paramtype version: str
        """
        parser = super(GnocchiShell, self).build_option_parser(description,
                                                               version)
        keystoneclient_cli.register_argparse_arguments(parser=parser,
                                                       argv=sys.argv,
                                                       default="password")
        return parser

    def initialize_app(self, argv):
        self.auth_plugin = keystoneclient_cli.load_from_argparse_arguments(
            self.options)
        self.client = client.Client(self.api_version, self.auth_plugin)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    # FIXME(sileht): read this from argv and env
    api_version = "1"
    return GnocchiShell(api_version).run(args)
