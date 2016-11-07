# -*- encoding: utf-8 -*-
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

import uuid

import pyparsing as pp
import six
from six.moves.urllib import parse as urllib_parse

uninary_operators = ("not", )
resource_binary_operator = (u">=", u"<=", u"!=", u">", u"<", u"=", u"==",
                            u"eq", u"ne", u"lt", u"gt", u"ge", u"le", u"in",
                            u"like", u"≠", u"≥", u"≤")
metric_binary_operator = (u">=", u"<=", u"!=", u">", u"<", u"=", u"==",
                          u"eq", u"ne", u"lt", u"gt", u"ge", u"le", u"≠",
                          u"≥", u"≤")
multiple_operators = (u"and", u"or", u"∧", u"∨")
null = pp.Regex("None|none|null").setParseAction(pp.replaceWith(None))
boolean = "False|True|false|true"
boolean = pp.Regex(boolean).setParseAction(lambda t: t[0].lower() == "true")
hex_string = lambda n: pp.Word(pp.hexnums, exact=n)
uuid_string = pp.Combine(hex_string(8) +
                         (pp.Optional("-") + hex_string(4)) * 3 +
                         pp.Optional("-") + hex_string(12))
number = r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?"
number = pp.Regex(number).setParseAction(lambda t: float(t[0]))
identifier = pp.Word(pp.alphas, pp.alphanums + "_")
quoted_string = pp.QuotedString('"') | pp.QuotedString("'")
comparison_term = pp.Forward()
in_list = pp.Group(pp.Suppress('[') +
                   pp.Optional(pp.delimitedList(comparison_term)) +
                   pp.Suppress(']'))("list")
comparison_term << (null | boolean | uuid_string | identifier | number |
                    quoted_string | in_list)


def _parsed_query2dict(parsed_query, binary_operator):
    result = None
    while parsed_query:
        part = parsed_query.pop()
        if part in binary_operator:
            try:
                result = {part: {parsed_query.pop(): result}}
            except IndexError:
                result = {part: result}

        elif part in multiple_operators:
            if result.get(part):
                result[part].append(
                    _parsed_query2dict(parsed_query.pop(), binary_operator))
            else:
                result = {part: [result]}

        elif part in uninary_operators:
            result = {part: result}
        elif isinstance(part, pp.ParseResults):
            kind = part.getName()
            if kind == "list":
                res = part.asList()
            else:
                res = _parsed_query2dict(part, binary_operator)
            if result is None:
                result = res
            elif isinstance(result, dict):
                list(result.values())[0].append(res)
        else:
            result = part
    return result


class MalformedQuery(Exception):
    def __init__(self, reason):
        super(MalformedQuery, self).__init__(
            "Malformed Query: %s" % reason)


def add_resource_query_argument(cmd, parser):
    return parser.add_argument(
        cmd,
        help=u"A query to filter resource. "
        u"The syntax is a combination of attribute, operator and value. "
        u"For example: id=90d58eea-70d7-4294-a49a-170dcdf44c3c would filter "
        u"resource with a certain id. More complex queries can be built, "
        u"e.g.: not (flavor_id!=\"1\" and memory>=24). "
        u"Use \"\" to force data to be interpreted as string. "
        u"Supported operators are: not, and, ∧ or, ∨, >=, <=, !=, >, <, =, "
        u"==, eq, ne, lt, gt, ge, le, in, like, ≠, ≥, ≤, like, in.",
        type=resource_query_builder)


def add_metric_query_argument(cmd, parser):
    return parser.add_argument(
        cmd,
        help=u"A query to filter metric value. "
        u"For example,'>= 50 and != 55' will look for all values that are "
        u"greater than or equal to 50 and that are not equal to 55"
        u"Supported operators are: not, and, ∧ or, ∨, >=, <=, !=, >, <, =, "
        u"==, eq, ne, lt, gt, ge, le, ≠, ≥, ≤.",
        type=metric_query_builder)


def build_expr(condition):
    expr = pp.operatorPrecedence(condition, [
                                ("not", 1, pp.opAssoc.RIGHT, ),
                                ("and", 2, pp.opAssoc.LEFT, ),
                                ("∧", 2, pp.opAssoc.LEFT, ),
                                ("or", 2, pp.opAssoc.LEFT, ),
                                ("∨", 2, pp.opAssoc.LEFT, ),
    ])
    return expr


def resource_query_builder(query):
    resource_operator = pp.Regex(u"|".join(resource_binary_operator))
    resource_condition = pp.Group(comparison_term + resource_operator
                                  + comparison_term)
    expr = build_expr(resource_condition)
    try:
        parsed_query = expr.parseString(query, parseAll=True)[0]
    except pp.ParseException as e:
        raise MalformedQuery(six.text_type(e))
    return _parsed_query2dict(parsed_query, resource_binary_operator)


def metric_query_builder(query):
    metric_operator = pp.Regex(u"|".join(metric_binary_operator))
    metric_condition = pp.Group(metric_operator + comparison_term)
    expr = build_expr(metric_condition)
    try:
        parsed_query = expr.parseString(query, parseAll=True)[0]
    except pp.ParseException as e:
        raise MalformedQuery(six.text_type(e))
    return _parsed_query2dict(parsed_query, metric_binary_operator)


def list2cols(cols, objs):
    return cols, [tuple([o[k] for k in cols])
                  for o in objs]


def format_string_list(l):
    return ", ".join(l)


def format_dict_list(l):
    return "\n".join(
        "- " + ", ".join("%s: %s" % (k, v)
                         for k, v in elem.items())
        for elem in l)


def format_dict_dict(value):
    return "\n".join(
        "- %s: " % name + " , ".join("%s: %s" % (k, v)
                                     for k, v in elem.items())
        for name, elem in value.items())


def format_move_dict_to_root(obj, field):
    for attr in obj[field]:
        obj["%s/%s" % (field, attr)] = obj[field][attr]
    del obj[field]


def format_resource_type(rt):
    format_move_dict_to_root(rt, "attributes")
    for key in rt:
        if key.startswith("attributes"):
            rt[key] = ", ".join(
                "%s=%s" % (k, v) for k, v in sorted(rt[key].items()))


def format_archive_policy(ap):
    ap['definition'] = format_dict_list(ap['definition'])
    ap['aggregation_methods'] = format_string_list(ap['aggregation_methods'])


def format_resource_for_metric(metric):
    # NOTE(sileht): Gnocchi < 2.0
    if 'resource' not in metric:
        return

    if not metric['resource']:
        metric['resource/id'] = None
        del metric['resource']
    else:
        format_move_dict_to_root(metric, "resource")


def dict_from_parsed_args(parsed_args, attrs):
    d = {}
    for attr in attrs:
        value = getattr(parsed_args, attr)
        if value is not None:
            d[attr] = value
    return d


def dict_to_querystring(objs):
    strings = []
    for k, values in sorted(objs.items()):
        if values is not None:
            if not isinstance(values, (list, tuple)):
                values = [values]
            strings.append("&".join(
                ("%s=%s" % (k, v)
                 for v in map(urllib_parse.quote,
                              map(six.text_type, values)))))
    return "&".join(strings)


def get_pagination_options(parsed_args):
    options = dict(
        sorts=parsed_args.sort,
        limit=parsed_args.limit,
        marker=parsed_args.marker)

    if hasattr(parsed_args, 'details'):
        options['details'] = parsed_args.details
    if hasattr(parsed_args, 'history'):
        options['history'] = parsed_args.history
    return options


def build_pagination_options(details=False, history=False,
                             limit=None, marker=None, sorts=None):
    options = []
    if details:
        options.append("details=true")
    if history:
        options.append("history=true")
    if limit:
        options.append("limit=%d" % limit)
    if marker:
        options.append("marker=%s" % urllib_parse.quote(marker))
    for sort in sorts or []:
        options.append("sort=%s" % urllib_parse.quote(sort))
    return "%s" % "&".join(options)


# uuid5 namespace for id transformation.
# NOTE(chdent): This UUID must stay the same, forever, across all
# of gnocchi to preserve its value as a URN namespace.
RESOURCE_ID_NAMESPACE = uuid.UUID('0a7a15ff-aa13-4ac2-897c-9bdf30ce175b')


def encode_resource_id(value):
    try:
        try:
            return str(uuid.UUID(value))
        except ValueError:
            if len(value) <= 255:
                if six.PY2:
                    value = value.encode('utf-8')
                return str(uuid.uuid5(RESOURCE_ID_NAMESPACE, value))
            raise ValueError(
                'transformable resource id >255 max allowed characters')
    except Exception as e:
        raise ValueError(e)


def get_client(obj):
    if hasattr(obj.app, 'client_manager'):
        # NOTE(sileht): cliff objects loaded by OSC
        return obj.app.client_manager.metric
    else:
        # TODO(sileht): Remove this when OSC is able
        # to install the gnocchi client binary itself
        return obj.app.client
