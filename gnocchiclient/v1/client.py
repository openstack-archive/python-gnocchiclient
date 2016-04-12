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

    :param string session: session
    :type session: :py:class:`keystoneauth.adapter.Adapter`
    """

    def __init__(self, session=None, service_type='metric', **kwargs):
        """Initialize a new client for the Gnocchi v1 API."""
        self.api = client.SessionClient(session, service_type=service_type,
                                        **kwargs)
        self.resource = resource.ResourceManager(self)
        self.resource_type = resource_type.ResourceTypeManager(self)
        self.archive_policy = archive_policy.ArchivePolicyManager(self)
        self.archive_policy_rule = (
            archive_policy_rule.ArchivePolicyRuleManager(self))
        self.metric = metric.MetricManager(self)
        self.capabilities = capabilities.CapabilitiesManager(self)
        self.status = status.StatusManager(self)
