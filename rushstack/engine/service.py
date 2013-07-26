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

import functools
import json

from oslo.config import cfg
import webob

from rushstack.openstack.common import timeutils
from rushstack.common import context
from rushstack.db import api as db_api
from rushstack.engine import api
from rushstack.rpc import api as rpc_api
from rushstack.engine import clients
from rushstack.common import identifier

from rushstack.openstack.common import log as logging
from rushstack.openstack.common import threadgroup
from rushstack.openstack.common.gettextutils import _
from rushstack.openstack.common.rpc import service
from rushstack.openstack.common import uuidutils
from rushstack.openstack.common import exception


logger = logging.getLogger(__name__)


def request_context(func):
    @functools.wraps(func)
    def wrapped(self, ctx, *args, **kwargs):
        if ctx is not None and not isinstance(ctx, context.RequestContext):
            ctx = context.RequestContext.from_dict(ctx.to_dict())
        return func(self, ctx, *args, **kwargs)
    return wrapped


class EngineService(service.Service):
    """
    Manages the running instances from creation to destruction.
    All the methods in here are called from the RPC backend.  This is
    all done dynamically so if a call is made via RPC that does not
    have a corresponding method here, an exception will be thrown when
    it attempts to call into this class.  Arguments to these methods
    are also dynamically added and will be named as keyword arguments
    by the RPC caller.
    """
    def __init__(self, host, topic, manager=None):
        super(EngineService, self).__init__(host, topic)

    def start(self):
        super(EngineService, self).start()

        # Create dummy service task, because when there is nothing queued
        # on self.tg the process exits
        self.tg.add_timer(cfg.CONF.periodic_interval,
                          self._service_task)

    def _service_task(self):
        """
        This is a dummy task which gets queued on the service.Service
        threadgroup.  Without this service.Service sees nothing running
        i.e has nothing to wait() on, so the process exits.
        This could also be used to trigger periodic non-stack-specific
        housekeeping tasks
        """
        pass

    def echo(self,cnxt,msg):
        '''
        Echo RPC backend method. Return the same msg between '*' 
        '''
        return '*%s*'%msg

    @request_context
    def get_status(self, ctxt,tenant_id):
        """
        Get Rush service status for the tenant (ctxt should contain tenant_id).

        :param ctxt: RPC context (must contain tenant_id)
        :param tenant_id: tenant_id to check for Rush
        
        Returns: JSON Specifying the status of rush and the id if present
        Response sample: {'result': True, 'active': True, 'rush_id': '8483934393'}
        """
        
        #Check in db if this tenant has an instanced Rush
        rt = db_api.rush_tenant_get_all_by_tenant(ctxt, tenant_id)
        if rt.first():
            logger.debug('tenant has rush:%s'%rt.first().rush_id)
            return {'result': True, 'active': True, 'rush_id': rt.first().rush_id}
        else:
            logger.debug('tenant has no rush')
            return {'result': True, 'active': False}

    @request_context
    def start_rush_stack(self, ctxt,tenant_id,rush_type_id):
        """
        Create new Rush service for the tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_type_id: rush_type_id for the new rush
        
        Returns: JSON Specifying the creation start result and the rush_id. Rush can take longer
                 to be ready for serving (check with get_status)
        Response sample: {'result': True, 'rush_id': '8483934393'}
        """
        
        #Check in db if this tenant has an instanced Rush
        rush_stat = self.get_status(ctxt,tenant_id)
        if rush_stat.has_key('active') and rush_stat['active']:
            return {'result': False, 'error': 'STARTRUSHEX01', 'error_desc': 'Rush already active'}
        else:
            try:
                #Check if type_id exists
                rtc = db_api.rush_type_get(ctxt,rush_type_id)
                if not rtc:
                    return {'result': False, 'error': 'STARTRUSHEX02', 'error_desc': 'Rush type does not exist'}
                    
                rush_id = uuidutils.generate_uuid()
                
                #TODO: Call HEAT and get the stack:id
                stack_id = ''
                values = {'stack_id':stack_id,'id':rush_id,'rush_type_id':rush_type_id,'status':'creating'}
                rc = db_api.rush_stack_create(ctxt, values)
                values = {'rush_id':rush_id,'tenant_id':tenant_id}
                tc = db_api.rush_tenant_create(ctxt, values)
                return {'result': True, 'rush_id': rush_id}
            except Exception as e:
                return {'result': False, 'error': str(e)}

    @request_context
    def stop_rush_stack(self, ctxt,tenant_id,rush_id):
        """
        Deletes the Rush service identified by rush_id for the tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_id: rush_id to stop
        
        Returns: JSON Specifying the stop result and the rush_id.
        Response sample: {'result': True, 'rush_id': '8483934393'}
        """
        
        #Check in db if this tenant has an instanced Rush
        rsc = db_api.rush_stack_get(ctxt,rush_id)
        if rsc:
            try:
                #Check if it is for this tenant
                rt = db_api.rush_tenant_get_all_by_tenant(ctxt, tenant_id)
                if not rt or rt.first().tenant_id != tenant_id:
                    return {'result': False, 'error': 'STOPRUSHEX02', 'error_desc': 'Could not find Rush for the tenant'}
                    
                #TODO: Call HEAT and stop the stack
                rt.delete()
                rsc.delete()
                return {'result': True, 'rush_id': rush_id}
            except Exception as e:
                return {'result': False, 'error': str(e)}
        else:
            return {'result': False, 'error': 'STOPRUSHEX01', 'error_desc': 'Could not find Rush'}

    @request_context
    def get_rush_endpoint(self, ctxt,tenant_id,rush_id):
        """
        Get the endpoint data for the Rush service identified by rush_id for the tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_id: rush_id to stop
        
        Returns: JSON Specifying the stop result and the rush_id.
        Response sample: {'result': True, 'rush_id': '8483934393', 'tk': '77389abbef92e01a0883d', 'ws': 'http://10.95.158.11/rush'}
        """
        
        #Check in db if the rush exists
        rsc = db_api.rush_stack_get(ctxt,rush_id)
        if rsc:
            try:
                #Check if it is for this tenant
                rt = db_api.rush_tenant_get_all_by_tenant(ctxt, tenant_id)
                if not rt or rt.first().tenant_id != tenant_id:
                    return {'result': False, 'error': 'GETRUSHEX02', 'error_desc': 'Could not find Rush for the tenant'}
                
                #Check if the data is fill in. If not, update
                #TODO: Call heat to update if necessary
                if rsc.tk is None:
                    #TODO: Go to get it
                    rsc.tk = "aabbccddeeff1234567890"
                if rsc.url is None:
                    #TODO: Go to get it
                    rsc.url = "http://10.98.28.23/"
                return {'result': True, 'rush_id': rush_id, 'tk': str(rsc.tk), 'url': str(rsc.url)}
            except Exception as e:
                return {'result': False, 'error': str(e)}
        else:
            return {'result': False, 'error': 'GETRUSHEX02', 'error_desc': 'Could not find Rush'}
                