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

from cliff import lister
from cliff import show


class ResourceList(lister.Lister):
    COLS = ('id', 'type',
            'project_id', 'user_id',
            'started_at', 'ended_at',
            'revision_start', 'revision_end')

    def get_parser(self, prog_name):
        parser = super(ResourceList, self).get_parser(prog_name)
        parser.add_argument("--details", action='store_true',
                            help="Show all attributes of generic resources"),
        parser.add_argument("--history", action='store_true',
                            help="Show history of the resources"),
        parser.add_argument("resource_type",
                            default="generic",
                            nargs='?',
                            help="Type of resource")
        return parser

    def take_action(self, parsed_args):
        resources = self.app.client.resource.list(
            resource_type=parsed_args.resource_type,
            details=parsed_args.details,
            history=parsed_args.history)
        return self.COLS, [self._resource2tuple(r) for r in resources]

    @classmethod
    def _resource2tuple(cls, resource):
        return tuple([resource[k] for k in cls.COLS])


class ResourceShow(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(ResourceShow, self).get_parser(prog_name)
        parser.add_argument("resource_type",
                            default="generic",
                            nargs='?',
                            help="Type of resource")
        parser.add_argument("resource_id",
                            help="ID of a resource")
        return parser

    def take_action(self, parsed_args):
        res = self.app.client.resource.get(
            resource_type=parsed_args.resource_type,
            resource_id=parsed_args.resource_id)
        res['metrics'] = "\n".join(sorted(
            ["%s: %s" % (name, _id)
             for name, _id in res['metrics'].items()]))
        return self.dict2columns(res)


class ResourceCreate(show.ShowOne):
    def get_parser(self, prog_name):
        parser = super(ResourceCreate, self).get_parser(prog_name)
        parser.add_argument("resource_type",
                            default="generic",
                            nargs='?',
                            help="Type of resource")
        parser.add_argument("--field", action='append',
                            help=("field and its value of a attribute "
                                  "separated with a ':'"))
        return parser

    def take_action(self, parsed_args):
        resource = {}
        if parsed_args.field:
            for field in parsed_args.field:
                field, __, value = field.partition(":")
                resource[field] = value
        res = self.app.client.resource.create(
            resource_type=parsed_args.resource_type, resource=resource)
        return self.dict2columns(res)
