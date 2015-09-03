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
            name=parsed_args.name)
        return self.dict2columns(res)


def archive_policy_definition(string):
    parts = string.split(",")
    defs = {}
    for part in parts:
        attr, __, value = part.partition(":")
        if (attr not in ['granularity', 'points', 'timespan']
                or value is None):
            raise ValueError
        defs[attr] = value
    if len(defs) < 2:
        raise ValueError
    return defs


class CliArchivePolicyCreate(show.ShowOne):

    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyCreate, self).get_parser(prog_name)
        parser.add_argument("name", help=("name of the active policy"))
        parser.add_argument("-b", "--back-window", dest="back_window",
                            type=int,
                            help=("back window of the active policy"))
        parser.add_argument("-m", "--aggregation-method",
                            action="append",
                            dest="aggregation_methods",
                            help=("aggregation method of the achive policy"))
        parser.add_argument("-d", "--definition", action='append',
                            required=True, type=archive_policy_definition,
                            metavar="<DEFINITION>",
                            help=("two attributes (separated by ',') of a "
                                  "archive policy defintion with its name and "
                                  "value separated with a ':'"))
        return parser

    def take_action(self, parsed_args):
        archive_policy = {}
        for attr in ['name', 'back_window', 'aggregation_methods']:
            value = getattr(parsed_args, attr)
            if value is not None:
                archive_policy[attr] = value
        archive_policy["definition"] = list(parsed_args.definition)
        policy = self.app.client.archivepolicy.create(
            archive_policy=archive_policy)
        return self.dict2columns(policy)


class CliArchivePolicyDelete(command.Command):
    def get_parser(self, prog_name):
        parser = super(CliArchivePolicyDelete, self).get_parser(prog_name)
        parser.add_argument("name",
                            help="Name of the archive policy")
        return parser

    def take_action(self, parsed_args):
        self.app.client.archivepolicy.delete(name=parsed_args.name)
