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
        req = utils.search_query_builder(expr)
        self.assertEqual(expected, req)

    def test_search_query_builder(self):
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
