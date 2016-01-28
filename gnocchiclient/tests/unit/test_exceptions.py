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
import json

from oslotest import base
from requests import models

from gnocchiclient import exceptions


class ExceptionsTest(base.BaseTestCase):
    def test_from_response_404(self):
        r = models.Response()
        r.status_code = 404
        r.headers['Content-Type'] = "application/json"
        r._content = json.dumps(
            {"description": "Archive policy rule foobar does not exist"}
        ).encode('utf-8')
        exc = exceptions.from_response(r)
        self.assertIsInstance(exc, exceptions.ArchivePolicyRuleNotFound)

    def test_from_response_keystone_401(self):
        r = models.Response()
        r.status_code = 401
        r.headers['Content-Type'] = "application/json"
        r._content = json.dumps({"error": {
            "message": "The request you have made requires authentication.",
            "code": 401, "title": "Unauthorized"}}
        ).encode('utf-8')
        exc = exceptions.from_response(r)
        self.assertIsInstance(exc, exceptions.Unauthorized)
        self.assertEqual("The request you have made requires authentication.",
                         exc.message)

    def test_from_response_unknown_middleware(self):
        r = models.Response()
        r.status_code = 400
        r.headers['Content-Type'] = "application/json"
        r._content = json.dumps(
            {"unknown": "random message"}
        ).encode('utf-8')
        exc = exceptions.from_response(r)
        self.assertIsInstance(exc, exceptions.ClientException)
        self.assertEqual('{"unknown": "random message"}', exc.message)
