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

import debtcollector
from debtcollector import removals
import keystoneauth1.session

from gnocchiclient import client
from gnocchiclient.v1 import archive_policy
from gnocchiclient.v1 import archive_policy_rule
from gnocchiclient.v1 import capabilities
from gnocchiclient.v1 import metric
from gnocchiclient.v1 import resource
from gnocchiclient.v1 import resource_type
from gnocchiclient.v1 import status


class Client(object):
    """Client for the Gnocchi v1 API.

    :param session: keystoneauth1 session
    :type session: :py:class:`keystoneauth1.session.Session` (optional)
    :param adapter_options: options to pass to
                            :py:class:`keystoneauth1.adapter.Adapter`
    :type adapter_options: dict (optional)
    :param session_options: options to pass to
                            :py:class:`keystoneauth1.session.Session`
    :type session_options: dict (optional)
    """

    @removals.removed_kwarg('service_type',
                            message="Please use 'adapter_options="
                            "dict(service_type=...)' instead")
    def __init__(self, session=None, service_type=None,
                 adapter_options=None, session_options=None,
                 **kwargs):
        """Initialize a new client for the Gnocchi v1 API."""
        session_options = session_options or {}
        adapter_options = adapter_options or {}

        adapter_options.setdefault('service_type', "metric")

        # NOTE(sileht): Backward compat stuff
        if kwargs:
            for key in kwargs:
                debtcollector.deprecate(
                    "Using the '%s' argument is deprecated" % key,
                    message="Please use 'adapter_options=dict(%s=...)' "
                    "instead" % key)
            adapter_options.update(kwargs)
        if service_type is not None:
            adapter_options['service_type'] = service_type

        if session is None:
            session = keystoneauth1.session.Session(**session_options)
        else:
            if session_options:
                raise ValueError("session and session_options are exclusive")

        self.api = client.SessionClient(session, **adapter_options)
        self.resource = resource.ResourceManager(self)
        self.resource_type = resource_type.ResourceTypeManager(self)
        self.archive_policy = archive_policy.ArchivePolicyManager(self)
        self.archive_policy_rule = (
            archive_policy_rule.ArchivePolicyRuleManager(self))
        self.metric = metric.MetricManager(self)
        self.capabilities = capabilities.CapabilitiesManager(self)
        self.status = status.StatusManager(self)
