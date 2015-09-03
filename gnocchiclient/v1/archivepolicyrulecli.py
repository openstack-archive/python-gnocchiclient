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

from cliff import command
from cliff import lister
from cliff import show

from gnocchiclient import utils


class CliArchivePolicyRuleList(lister.Lister):
    COLS = ('archive_policy_name', 'metric_pattern', 'name')

    def get_parser(self, prog_name, history=True):
        parser = super(CliArchivePolicyRuleList, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        ap_rules = self.app.client.archivepolicyrule.list(parsed_args)
        return utils.list2cols(self.COLS, ap_rules)


class CliArchivePolicyRuleShow(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyRuleShow, self).get_parser(prog_name)
        parser.add_argument("name",
                            help="Name of the archive policy rule")
        return parser

    def take_action(self, parsed_args):
        ap_rule = self.app.client.archivepolicyrule.get(
            policy_rule_name=parsed_args.name)
        return self.dict2columns(ap_rule)


class CliArchivePolicyRuleCreate(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyRuleCreate, self).get_parser(prog_name)
        parser.add_argument("-a", "--attribute", action='append',
                            help=("name and value of a attribute "
                                  "separated with a ':'"))
        return parser

    def take_action(self, parsed_args):
        data = {}
        if parsed_args.attribute:
            for attr in parsed_args.attribute:
                attr, __, value = attr.partition(":")
                data[attr] = value
        policy = self.app.client.archivepolicyrule.create(data=data)
        return self.dict2columns(policy)


class CliArchivePolicyRuleDelete(command.Command):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyRuleDelete, self).get_parser(prog_name)
        parser.add_argument("name",
                            help="Name of the archive policy rule")
        return parser

    def take_action(self, parsed_args):
        self.app.client.archivepolicyrule.delete(parsed_args.name)
