# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from heatclient import client as heat_client
from oslo.config import cfg
from keystoneclient.v2_0 import client as ksclient

LOG = logging.getLogger(__name__)


def format_parameters(params):
    parameters = {}
    for count, p in enumerate(params, 1):
        parameters['Parameters.member.%d.ParameterKey' % count] = p
        parameters['Parameters.member.%d.ParameterValue' % count] = params[p]
    return parameters

def _get_ksclient(**kwargs):
    """Get an endpoint and auth token from Keystone.

    :param username: name of user
    :param password: user's password
    :param tenant_id: unique identifier of tenant
    :param tenant_name: name of tenant
    :param auth_url: endpoint to authenticate against
    """
    return ksclient.Client(username=kwargs.get('username'),
                           password=kwargs.get('password'),
                           tenant_id=kwargs.get('tenant_id'),
                           tenant_name=kwargs.get('tenant_name'),
                           auth_url=kwargs.get('auth_url'),
                           insecure=kwargs.get('insecure'))

def heatclient(username=None,password=None,tenant_name=None):
    api_version = "1"
    insecure = False
    kwargs = {
        'username': username,
        'password': password,
        'tenant_id': None,
        'tenant_name': tenant_name,
        'auth_url': cfg.CONF.auth_uri,
        #'service_type': args.os_service_type,
        #'endpoint_type': cfg.CONF.orchestration_type,
        'insecure': insecure
    }
    ksclient = _get_ksclient(**kwargs)
    kwargs['token'] = ksclient.auth_token

    #Get the endpoint
    endpoint = ksclient.service_catalog.get_endpoints(cfg.CONF.orchestration_type)[cfg.CONF.orchestration_type][0]['publicURL']
    
    client = heat_client.Client(api_version, endpoint, **kwargs)
    client.format_parameters = format_parameters
    return client

def stacks_list(request):
    return heatclient(request).stacks.list()


def stack_delete(request, stack_id):
    return heatclient(request).stacks.delete(stack_id)


def stack_get(request, stack_id):
    return heatclient(request).stacks.get(stack_id)


def stack_create(request, password=None, **kwargs):
    return heatclient(request, password).stacks.create(**kwargs)


def events_list(request, stack_name):
    return heatclient(request).events.list(stack_name)


def resources_list(request, stack_name):
    return heatclient(request).resources.list(stack_name)


def resource_get(request, stack_id, resource_name):
    return heatclient(request).resources.get(stack_id, resource_name)


def resource_metadata_get(request, stack_id, resource_name):
    return heatclient(request).resources.metadata(stack_id, resource_name)


def template_validate(request, **kwargs):
    return heatclient(request).stacks.validate(**kwargs)
