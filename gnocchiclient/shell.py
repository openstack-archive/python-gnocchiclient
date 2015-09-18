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

import argparse
import logging
import os
import sys
import warnings

from cliff import app
from cliff import commandmanager
from keystoneclient.auth import cli as keystoneclient_cli
from keystoneclient import exceptions

from gnocchiclient import client
from gnocchiclient import noauth
from gnocchiclient.version import __version__

LOG = logging.getLogger(__name__)


def _positive_non_zero_int(argument_value):
    if argument_value is None:
        return None
    try:
        value = int(argument_value)
    except ValueError:
        msg = "%s must be an integer" % argument_value
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % argument_value
        raise argparse.ArgumentTypeError(msg)
    return value


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
        # Global arguments
        parser.add_argument(
            '--os-region-name',
            metavar='<auth-region-name>',
            dest='region_name',
            default=os.environ.get('OS_REGION_NAME'),
            help='Authentication region name (Env: OS_REGION_NAME)')
        parser.add_argument(
            '--os-cacert',
            metavar='<ca-bundle-file>',
            dest='cacert',
            default=os.environ.get('OS_CACERT'),
            help='CA certificate bundle file (Env: OS_CACERT)')
        verify_group = parser.add_mutually_exclusive_group()
        verify_group.add_argument(
            '--verify',
            action='store_true',
            default=None,
            help='Verify server certificate (default)',
        )
        verify_group.add_argument(
            '--insecure',
            action='store_true',
            default=None,
            help='Disable server certificate verification',
        )
        parser.add_argument(
            '--os-interface',
            metavar='<interface>',
            dest='interface',
            choices=['admin', 'public', 'internal'],
            default=os.environ.get('OS_INTERFACE'),
            help='Select an interface type.'
                 ' Valid interface types: [admin, public, internal].'
                 ' (Env: OS_INTERFACE)')

        parser.add_argument('--timeout',
                            default=600,
                            type=_positive_non_zero_int,
                            help='Number of seconds to wait for a response.')

        plugin = keystoneclient_cli.register_argparse_arguments(
            parser=parser, argv=sys.argv, default="password")

        if plugin != noauth.GnocchiNoAuthPlugin:
            parser.add_argument(
                '--gnocchi-endpoint',
                metavar='<endpoint>',
                dest='endpoint',
                default=os.environ.get('GNOCCHI_ENDPOINT'),
                help='Gnocchi endpoint (Env: GNOCCHI_ENDPOINT)')

        return parser

    def initialize_app(self, argv):
        super(GnocchiShell, self).initialize_app(argv)
        if hasattr(self.options, "endpoint"):
            endpoint = self.options.endpoint
        else:
            endpoint = None
        auth_plugin = keystoneclient_cli.load_from_argparse_arguments(
            self.options)
        self.client = client.Client(self.api_version,
                                    auth=auth_plugin,
                                    endpoint=endpoint,
                                    region_name=self.options.region_name,
                                    interface=self.options.interface,
                                    verify=self.options.verify,
                                    cert=self.options.cacert,
                                    timeout=self.options.timeout)

    def clean_up(self, cmd, result, err):
        if err and isinstance(err, exceptions.HttpError):
            print(err.details)

    def configure_logging(self):
        if self.options.debug:
            # --debug forces verbose_level 3
            # Set this here so cliff.app.configure_logging() can work
            self.options.verbose_level = 3

        super(GnocchiShell, self).configure_logging()
        root_logger = logging.getLogger('')

        # Set logging to the requested level
        if self.options.verbose_level == 0:
            # --quiet
            root_logger.setLevel(logging.ERROR)
            warnings.simplefilter("ignore")
        elif self.options.verbose_level == 1:
            # This is the default case, no --debug, --verbose or --quiet
            root_logger.setLevel(logging.WARNING)
            warnings.simplefilter("ignore")
        elif self.options.verbose_level == 2:
            # One --verbose
            root_logger.setLevel(logging.INFO)
            warnings.simplefilter("once")
        elif self.options.verbose_level >= 3:
            # Two or more --verbose
            root_logger.setLevel(logging.DEBUG)

        # Hide some useless message
        requests_log = logging.getLogger("requests")
        cliff_log = logging.getLogger('cliff')
        stevedore_log = logging.getLogger('stevedore')
        iso8601_log = logging.getLogger("iso8601")

        cliff_log.setLevel(logging.ERROR)
        stevedore_log.setLevel(logging.ERROR)
        iso8601_log.setLevel(logging.ERROR)

        if self.options.debug:
            requests_log.setLevel(logging.DEBUG)
        else:
            requests_log.setLevel(logging.ERROR)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    # FIXME(sileht): read this from argv and env
    api_version = "1"
    return GnocchiShell(api_version).run(args)
