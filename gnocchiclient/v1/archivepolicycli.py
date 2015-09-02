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


class CliArchivePolicyList(lister.Lister):
    COLS = ('name',
            'back_window', 'definition', 'aggregation_methods')

    def get_parser(self, prog_name, history=True):
        parser = super(CliArchivePolicyList, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        policy = self.app.client.archivepolicy.list(parsed_args)
        return self.COLS, [self._2tuple(r) for r in policy]

    @classmethod
    def _2tuple(cls, field):
        return tuple([field[k] for k in cls.COLS])


class CliArchivePolicyShow(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyShow, self).get_parser(prog_name)
        parser.add_argument("name",
                            help="Name of the archive policy")
        return parser

    def take_action(self, parsed_args):
        res = self.app.client.archivepolicy.get(
            policy_name=parsed_args.name)
        return self.dict2columns(res)


class CliArchivePolicyCreate(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyCreate, self).get_parser(prog_name)
        parser.add_argument("-a", "--attribute", action='append',
                            help=("name and value of a attribute "
                                  "separated with a ':'"))
        parser.add_argument("-d", "--definition", action='append',
                            help=("name and value of a attribute "
                                  "separated with a ':'"))
        return parser

    def take_action(self, parsed_args):
        data = {}
        if parsed_args.attribute:
            for attr in parsed_args.attribute:
                attr, __, value = attr.partition(":")
                data[attr] = value
        if parsed_args.definition:
            definition = {}
            data["definition"] = []
            for attr in parsed_args.definition:
                attr, __, value = attr.partition(":")
                definition[attr] = value
            data["definition"].append(definition)
        policy = self.app.client.archivepolicy.create(data=data)
        return self.dict2columns(policy)


class CliArchivePolicyDelete(command.Command):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyDelete, self).get_parser(prog_name)
        parser.add_argument("name",
                            help="Name of the archive policy")
        return parser

    def take_action(self, parsed_args):
        self.app.client.archivepolicy.delete(parsed_args.name)
