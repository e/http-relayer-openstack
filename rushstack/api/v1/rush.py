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
Stack endpoint for Heat v1 ReST API.
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
    WSGI controller for stacks resource in Heat v1 API
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
        Echo test method for Rush API
        """

        return {'req': str(req), 'req.context': str(req.context.to_dict())}
    
    @util.tenant_local
    def getStatus(self, req):
        """
        Get status of RUSH service for this tenant
        """
        #TODO: Implement call to RPC to get real status and if active, return internal ID
        return {'result': True, 'active': False}
    
    ACTIONS = (STOP, START) = ('stop', 'start')
    
    @util.tenant_local
    def changeStatus(self, req, body={}):
        """
        Change status of RUSH service for this tenant
        Only 1 action must be specified
        """

        if len(body) < 1:
            raise exc.HTTPBadRequest(_("No action specified."))

        if len(body) > 1:
            raise exc.HTTPBadRequest(_("Multiple actions specified"))

        ac = body.keys()[0]
        if ac not in self.ACTIONS:
            raise exc.HTTPBadRequest(_("Invalid action %s specified") % ac)
        
        #TODO: Implement call to RPC to chage status
        if ac == self.STOP:
            return {'result': True, 'active': False}
        elif ac == self.START:
            return {'result': True, 'active': True}
        else:
            raise exc.HTTPInternalServerError(_("Unexpected action %s") % ac)
    
    @util.identified_rush
    def getUserEndpoind(self, req):
        """
        Get tenant RUSH endpoint data
        """
        
        #TODO: Implement call to RPC to get real status and if active, return internal ID
        return {'result': True, 'rush_id': req.context.rush_id, 'tk': '77389abbef92e01a0883d', 'ws': 'http://10.95.158.11/rush'}
    
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
