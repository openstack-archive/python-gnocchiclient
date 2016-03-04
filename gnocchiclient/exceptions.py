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

import re


class ClientException(Exception):
    """The base exception class for all exceptions this library raises."""
    message = 'Unknown Error'

    def __init__(self, code=None, message=None, request_id=None,
                 url=None, method=None):
        self.code = code
        self.message = message or self.__class__.message
        self.request_id = request_id
        self.url = url
        self.method = method

    def __str__(self):
        formatted_string = "%s" % self.message
        if self.code:
            formatted_string += " (HTTP %s)" % self.code
        if self.request_id:
            formatted_string += " (Request-ID: %s)" % self.request_id
        return formatted_string


class RetryAfterException(ClientException):
    """The base exception for ClientExceptions that use Retry-After header."""
    def __init__(self, *args, **kwargs):
        try:
            self.retry_after = int(kwargs.pop('retry_after'))
        except (KeyError, ValueError):
            self.retry_after = 0

        super(RetryAfterException, self).__init__(*args, **kwargs)


class MutipleMeaningException(object):
    """An mixin for exception that can be enhanced by reading the details"""


class BadRequest(ClientException):
    """HTTP 400 - Bad request: you sent some malformed data."""
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """HTTP 401 - Unauthorized: bad credentials."""
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """HTTP 403 - Forbidden:

    your credentials don't give you access to this resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """HTTP 404 - Not found"""
    http_status = 404
    message = "Not found"


class MetricNotFound(NotFound, MutipleMeaningException):
    message = "Metric not found"
    match = re.compile("Metric .* does not exist")


class ResourceNotFound(NotFound, MutipleMeaningException):
    message = "Resource not found"
    match = re.compile("Resource .* does not exist")


class ArchivePolicyNotFound(NotFound, MutipleMeaningException):
    message = "Archive policy not found"
    match = re.compile("Archive policy .* does not exist")


class ArchivePolicyRuleNotFound(NotFound, MutipleMeaningException):
    message = "Archive policy rule not found"
    match = re.compile("Archive policy rule .* does not exist")


class MethodNotAllowed(ClientException):
    """HTTP 405 - Method Not Allowed"""
    http_status = 405
    message = "Method Not Allowed"


class NotAcceptable(ClientException):
    """HTTP 406 - Not Acceptable"""
    http_status = 406
    message = "Not Acceptable"


class Conflict(ClientException):
    """HTTP 409 - Conflict"""
    http_status = 409
    message = "Conflict"


class NamedMetricAlreadyExists(Conflict, MutipleMeaningException):
    message = "Named metric already exists"
    match = re.compile("Named metric .* does not exist")


class ResourceAlreadyExists(Conflict, MutipleMeaningException):
    message = "Resource already exists"
    match = re.compile("Resource .* already exists")


class ArchivePolicyAlreadyExists(Conflict, MutipleMeaningException):
    message = "Archive policy already exists"
    match = re.compile("Archive policy .* already exists")


class ArchivePolicyRuleAlreadyExists(Conflict, MutipleMeaningException):
    message = "Archive policy rule already exists"
    match = re.compile("Archive policy rule .* already exists")


class OverLimit(RetryAfterException):
    """HTTP 413 - Over limit:

    you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


class RateLimit(RetryAfterException):
    """HTTP 429 - Rate limit:

    you've sent too many requests for this time period.
    """
    http_status = 429
    message = "Rate limit"


class NotImplemented(ClientException):
    """HTTP 501 - Not Implemented:

    the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


_error_classes = [BadRequest, Unauthorized, Forbidden, NotFound,
                  MethodNotAllowed, NotAcceptable, Conflict, OverLimit,
                  RateLimit, NotImplemented]
_error_classes_enhanced = {
    NotFound: [MetricNotFound, ResourceNotFound, ArchivePolicyRuleNotFound,
               ArchivePolicyNotFound],
    Conflict: [NamedMetricAlreadyExists, ResourceAlreadyExists,
               ArchivePolicyAlreadyExists,
               ArchivePolicyRuleAlreadyExists]
}
_code_map = dict(
    (c.http_status, (c, _error_classes_enhanced.get(c, [])))
    for c in _error_classes)


def from_response(response, method=None):
    """Return an instance of one of the ClientException on an requests response.

    Usage::

        resp, body = requests.request(...)
        if resp.status_code != 200:
            raise from_response(resp)
    """

    if response.status_code:
        cls, enhanced_classes = _code_map.get(response.status_code,
                                              (ClientException, []))

    req_id = response.headers.get("x-openstack-request-id")
    content_type = response.headers.get("Content-Type", "").split(";")[0]

    kwargs = {
        'code': response.status_code,
        'method': method,
        'url': response.url,
        'request_id': req_id,
    }

    if "retry-after" in response.headers:
        kwargs['retry_after'] = response.headers.get('retry-after')

    if content_type == "application/json":
        try:
            body = response.json()
        except ValueError:
            pass
        else:
            if 'description' in body:
                # Gnocchi json
                desc = body.get('description')
                if desc:
                    for enhanced_cls in enhanced_classes:
                        if enhanced_cls.match.match(desc):
                            cls = enhanced_cls
                            break
                kwargs['message'] = desc
            elif isinstance(body, dict) and isinstance(body.get("error"),
                                                       dict):
                # Keystone json
                kwargs['message'] = body["error"]["message"]
            else:
                kwargs['message'] = response.text
    elif content_type.startswith("text/"):
        kwargs['message'] = response.text

    if not kwargs['message']:
        del kwargs['message']
    return cls(**kwargs)
