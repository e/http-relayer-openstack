# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from keystoneclient.v2_0 import client as kc

from rushstack.openstack.common import log as logging

logger = logging.getLogger('rushstack.common.keystoneclient')


class KeystoneClient(object):
    """
    Wrap keystone client so we can encapsulate logic used in resources
    Note this is intended to be initialized from a resource on a per-session
    basis, so the session context is passed in on initialization
    Also note that a copy of this is created every resource as self.keystone()
    via the code in engine/client.py, so there should not be any need to
    directly instantiate instances of this class inside resources themselves
    """
    def __init__(self, context):
        self.context = context
        kwargs = {
            'auth_url': context.auth_url,
        }

        if context.password is not None:
            kwargs['username'] = context.username
            kwargs['password'] = context.password
            kwargs['tenant_name'] = context.tenant
            kwargs['tenant_id'] = context.tenant_id
        elif context.auth_token is not None:
            kwargs['tenant_name'] = context.tenant
            kwargs['token'] = context.auth_token
        else:
            logger.error("Keystone connection failed, no password or " +
                         "auth_token!")
            return
        self.client = kc.Client(**kwargs)
        self.client.authenticate()

    def url_for(self, **kwargs):
        return self.client.service_catalog.url_for(**kwargs)

    @property
    def auth_token(self):
        return self.client.auth_token
