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

import logging
import os
import sys
import warnings

from cliff import app
from cliff import commandmanager
from keystoneauth1 import adapter
from keystoneauth1 import exceptions
from keystoneauth1 import loading

from gnocchiclient import client
from gnocchiclient import noauth
from gnocchiclient.v1 import archive_policy_cli
from gnocchiclient.v1 import archive_policy_rule_cli as ap_rule_cli
from gnocchiclient.v1 import capabilities_cli
from gnocchiclient.v1 import metric_cli
from gnocchiclient.v1 import resource_cli
from gnocchiclient.version import __version__


class GnocchiCommandManager(commandmanager.CommandManager):
    SHELL_COMMANDS = {
        "resource list": resource_cli.CliResourceList,
        "resource show": resource_cli.CliResourceShow,
        "resource history": resource_cli.CliResourceHistory,
        "resource search": resource_cli.CliResourceSearch,
        "resource create": resource_cli.CliResourceCreate,
        "resource update": resource_cli.CliResourceUpdate,
        "resource delete": resource_cli.CliResourceDelete,
        "archive-policy list": archive_policy_cli.CliArchivePolicyList,
        "archive-policy show": archive_policy_cli.CliArchivePolicyShow,
        "archive-policy create": archive_policy_cli.CliArchivePolicyCreate,
        "archive-policy delete": archive_policy_cli.CliArchivePolicyDelete,
        "archive-policy-rule list": ap_rule_cli.CliArchivePolicyRuleList,
        "archive-policy-rule show": ap_rule_cli.CliArchivePolicyRuleShow,
        "archive-policy-rule create": ap_rule_cli.CliArchivePolicyRuleCreate,
        "archive-policy-rule delete": ap_rule_cli.CliArchivePolicyRuleDelete,
        "metric list": metric_cli.CliMetricList,
        "metric show": metric_cli.CliMetricShow,
        "metric create": metric_cli.CliMetricCreate,
        "metric delete": metric_cli.CliMetricDelete,
        "measures get": metric_cli.CliMeasuresGet,
        "measures add": metric_cli.CliMeasuresAdd,
        "measures aggregation": metric_cli.CliMeasuresAggregation,
        "capabilities list": capabilities_cli.CliCapabilitiesList,
    }

    def load_commands(self, namespace):
        for name, command_class in self.SHELL_COMMANDS.items():
            self.add_command(name, command_class)


class GnocchiShell(app.App):
    def __init__(self, api_version):
        super(GnocchiShell, self).__init__(
            description='Gnocchi command line client',
            # FIXME(sileht): get version from pbr
            version=__version__,
            command_manager=GnocchiCommandManager(None),
            deferred_help=True,
            )

        self.api_version = api_version
        self._client = None

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
        # Global arguments, one day this should go to keystoneauth1
        parser.add_argument(
            '--os-region-name',
            metavar='<auth-region-name>',
            dest='region_name',
            default=os.environ.get('OS_REGION_NAME'),
            help='Authentication region name (Env: OS_REGION_NAME)')
        parser.add_argument(
            '--os-interface',
            metavar='<interface>',
            dest='interface',
            choices=['admin', 'public', 'internal'],
            default=os.environ.get('OS_INTERFACE'),
            help='Select an interface type.'
                 ' Valid interface types: [admin, public, internal].'
                 ' (Env: OS_INTERFACE)')

        loading.register_session_argparse_arguments(parser=parser)
        plugin = loading.register_auth_argparse_arguments(
            parser=parser, argv=sys.argv, default="password")

        if not isinstance(plugin, noauth.GnocchiNoAuthLoader):
            parser.add_argument(
                '--gnocchi-endpoint',
                metavar='<endpoint>',
                dest='endpoint',
                default=os.environ.get('GNOCCHI_ENDPOINT'),
                help='Gnocchi endpoint (Env: GNOCCHI_ENDPOINT)')

        return parser

    @property
    def client(self):
        # NOTE(sileht): we lazy load the client to not
        # load/connect auth stuffs
        if self._client is None:
            if hasattr(self.options, "endpoint"):
                endpoint_override = self.options.endpoint
            else:
                endpoint_override = None
            auth_plugin = loading.load_auth_from_argparse_arguments(
                self.options)
            session = loading.load_session_from_argparse_arguments(
                self.options, auth=auth_plugin)

            session = adapter.Adapter(session, service_type='metric',
                                      interface=self.options.interface,
                                      region_name=self.options.region_name,
                                      endpoint_override=endpoint_override)

            self._client = client.Client(self.api_version, session=session)
        return self._client

    def clean_up(self, cmd, result, err):
        if err and isinstance(err, exceptions.HttpError):
            try:
                error = err.response.json()
            except Exception:
                pass
            else:
                print(error['description'])

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
