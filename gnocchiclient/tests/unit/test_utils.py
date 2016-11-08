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

from oslotest import base

from gnocchiclient import utils


class SearchQueryBuilderTest(base.BaseTestCase):
    def _do_test(self, expr, expected):
        req = utils.resource_query_builder(expr)
        self.assertEqual(expected, req)

    def _do_metric_test(self, expr, expected):
        req = utils.resource_query_builder(expr)
        self.assertEqual(expected, req)

    def test_resource_query_builder(self):
        self._do_test('foo=7EED6CC3-EDC8-48C9-8EF6-8A36B9ACC91C',
                      {"=": {"foo": "7EED6CC3-EDC8-48C9-8EF6-8A36B9ACC91C"}})
        self._do_test('foo=7EED6CC3EDC848C98EF68A36B9ACC91C',
                      {"=": {"foo": "7EED6CC3EDC848C98EF68A36B9ACC91C"}})
        self._do_test('foo=bar', {"=": {"foo": "bar"}})
        self._do_test('foo!=1', {"!=": {"foo": 1.0}})
        self._do_test('foo=True', {"=": {"foo": True}})
        self._do_test('foo=null', {"=": {"foo": None}})
        self._do_test('foo="null"', {"=": {"foo": "null"}})
        self._do_test('foo in ["null", "foo"]',
                      {"in": {"foo": ["null", "foo"]}})
        self._do_test(u'foo="quote" and bar≠1',
                      {"and": [{u"≠": {"bar": 1}},
                               {"=": {"foo": "quote"}}]})
        self._do_test('foo="quote" or bar like "%%foo"',
                      {"or": [{"like": {"bar": "%%foo"}},
                              {"=": {"foo": "quote"}}]})

        self._do_test('not (foo="quote" or bar like "%%foo" or foo="what!" '
                      'or bar="who?")',
                      {"not": {"or": [
                          {"=": {"bar": "who?"}},
                          {"=": {"foo": "what!"}},
                          {"like": {"bar": "%%foo"}},
                          {"=": {"foo": "quote"}},
                      ]}})

        self._do_test('(foo="quote" or bar like "%%foo" or not foo="what!" '
                      'or bar="who?") and cat="meme"',
                      {"and": [
                          {"=": {"cat": "meme"}},
                          {"or": [
                              {"=": {"bar": "who?"}},
                              {"not": {"=": {"foo": "what!"}}},
                              {"like": {"bar": "%%foo"}},
                              {"=": {"foo": "quote"}},
                          ]}
                      ]})

        self._do_test('foo="quote" or bar like "%%foo" or foo="what!" '
                      'or bar="who?" and cat="meme"',
                      {"or": [
                          {"and": [
                              {"=": {"cat": "meme"}},
                              {"=": {"bar": "who?"}},
                          ]},
                          {"=": {"foo": "what!"}},
                          {"like": {"bar": "%%foo"}},
                          {"=": {"foo": "quote"}},
                      ]})

        self._do_test('foo="quote" or bar like "%%foo" and foo="what!" '
                      'or bar="who?" or cat="meme"',
                      {"or": [
                          {"=": {"cat": "meme"}},
                          {"=": {"bar": "who?"}},
                          {"and": [
                              {"=": {"foo": "what!"}},
                              {"like": {"bar": "%%foo"}},
                          ]},
                          {"=": {"foo": "quote"}},
                      ]})

    def test_metric_query_builder(self):
        self._test_metric('= 12', {'=': 12})
        self._test_metric('>= 15 and < 20', {'and': [{'>=': 15}, {'<': 20}]})
        self._test_metric('> 15 and != 20', {'and': [{'>': 15}, {'!=': 20}]})

    def test_dict_to_querystring(self):
        expected = ["start=2016-02-10T13%3A54%3A53%2B00%3A00"
                    "&stop=2016-02-10T13%3A56%3A42%2B02%3A00",
                    "stop=2016-02-10T13%3A56%3A42%2B02%3A00"
                    "&start=2016-02-10T13%3A54%3A53%2B00%3A00"]

        self.assertIn(utils.dict_to_querystring(
            {"start": "2016-02-10T13:54:53+00:00",
             "stop": "2016-02-10T13:56:42+02:00"}),
            expected)

        self.assertEqual(
            "groupby=foo&groupby=bar",
            utils.dict_to_querystring({
                "groupby": ["foo", "bar"]
            }),
        )

        self.assertEqual(
            "groupby=foo&groupby=bar&overlap=0",
            utils.dict_to_querystring({
                "groupby": ["foo", "bar"],
                "overlap": 0,
            }),
        )
