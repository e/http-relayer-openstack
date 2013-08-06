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

"""
Stack endpoint for RUSH v1 ReST API.
"""

from webob import exc

from rushstack.api.v1 import util
from rushstack.openstack.common import wsgi
from rushstack.rpc import api as engine_api
from rushstack.rpc import client as rpc_client

from rushstack.openstack.common import log as logging
from rushstack.openstack.common.gettextutils import _

logger = logging.getLogger(__name__)

class RushController(object):
    """
    WSGI controller for stacks resource in RUSH v1 API
    Implements the API actions
    """

    def __init__(self, options):
        self.options = options
        self.engine = rpc_client.EngineClient()

    def default(self, req, **args):
        raise exc.HTTPNotFound()

    '''Rushstack methods
    '''
    @util.tenant_local
    def echo(self, req):
        """
        Echo test method for Rush API - Sends echo request to RPC backend
        """
        res = self.engine.echo(req.context,'Test message')
        return {'tenant_id': req.context.tenant_id, 'res': res}
    
    @util.tenant_local
    def get_status(self, req):
        """
        Get status of RUSH service for this tenant and id
        """
        return self.engine.get_status(req.context,req.context.tenant_id)
    
    ACTIONS = (STOP, START) = ('stop', 'start')
    
    @util.tenant_local
    def create_rush(self, req, body={}):
        """
        Create RUSH service for this tenant
        Body must contain the rush_type_id
        """
        return self.engine.start_rush_stack(req.context,req.context.tenant_id,body['rush_type_id'])
    
    @util.identified_rush
    def delete_rush(self, req):
        """
        Delete RUSH service for this tenant
        """
        return self.engine.stop_rush_stack(req.context,req.context.tenant_id,req.context.rush_id)
    
    @util.identified_rush
    def get_rush_endpoind(self, req):
        """
        Get tenant RUSH endpoint data
        """
        
        #Call to RPC to get real status and if active, return URL and Token
        return self.engine.get_rush_endpoint(req.context,req.context.tenant_id,req.context.rush_id)
    
class RushSerializer(wsgi.JSONResponseSerializer):
    """Handles serialization of specific controller method responses."""

    def _populate_response_header(self, response, location, status):
        response.status = status
        response.headers['Location'] = location.encode('utf-8')
        response.headers['Content-Type'] = 'application/json'
        return response

    def create(self, response, result):
        self._populate_response_header(response,
                                       result['stack']['links'][0]['href'],
                                       201)
        response.body = self.to_json(result)
        return response


def create_resource(options):
    """
    Rush resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = RushSerializer()
    return wsgi.Resource(RushController(options), deserializer, serializer)
