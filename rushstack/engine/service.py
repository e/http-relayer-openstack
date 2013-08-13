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

from rushstack.openstack.common import log as logging
from rushstack.openstack.common import threadgroup
from rushstack.openstack.common.gettextutils import _
from rushstack.openstack.common.rpc import service
from rushstack.openstack.common import uuidutils
from rushstack.openstack.common import exception
from rushstack.heatapi import heat

import json


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
        logger.warning('periodic_interval:'+str(cfg.CONF.periodic_interval))
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
    def get_list(self, ctxt,tenant_id):
        """
        Get Rush service list for the tenant (ctxt should contain tenant_id).

        :param ctxt: RPC context (must contain tenant_id)
        :param tenant_id: tenant_id to check for Rush
        
        Returns: JSON Specifying the list of rush services and their data
        Response sample: {'result': True, 'rush_services': [{'id': '8483934393','name':'Rush prepro','type':1 ,'endpoint': 'http://10.1.1.1:5001', 'status': 'CREATE_COMPLETE' }]}
        """
        
        try:
            #Check in db if this tenant has an instanced Rush
            rt = db_api.rush_tenant_get_all_by_tenant(ctxt, tenant_id)
            result = {'result': True, 'rushes': []}
            for rtentry in rt:
                rush_entry = db_api.rush_stack_get(ctxt, rtentry.rush_id)
                
                #Update status with heat data (Rushstack DB can be out of sync with HEAT stack status)
                #Can be removed to improve query performance when status is CREATE_COMPLETE
                heatcln = heat.heatclient(cfg.CONF.tdaf_username, cfg.CONF.tdaf_user_password, cfg.CONF.tdaf_tenant_name)
                
                rush_stack_name = cfg.CONF.tdaf_rush_prefix+str(tenant_id)+"-"+str(rush_entry.name)
                stack_list = self.get_stack_list_for_tenant(heatcln,tenant_id)
                for stack in stack_list:
                    stack_info = stack._info;
                    if stack_info['stack_name'] == rush_stack_name:
                        break
                        
                if stack_info is not None and stack_info['stack_name'] == rush_stack_name:
                    #Stack info first
                    values = {'status':stack_info['stack_status']}
                    db_api.rush_stack_update(ctxt, rtentry.rush_id, values)
                    
                self.update_rush_endpointdata(ctxt,heatcln,rush_entry.stack_id,rtentry.rush_id)
                result['rushes'].append({'id': rush_entry.id, 'name': rush_entry.name, 'type': rush_entry.rush_type_id,
                                         'endpoint':rush_entry.url, 'status': rush_entry.status})
            return result
        except Exception as e:
            return {'result': False, 'error': str(e)}

    @request_context
    def start_rush_stack(self, ctxt,tenant_id,rush_type_id, rush_name):
        """
        Create new Rush service for the tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_type_id: rush_type_id for the new rush
        :param rush_name: rush name to use for this new rush
        
        Returns: JSON Specifying the creation start result and the rush_id. Rush can take longer
                 to be ready for serving (check with get_status)
        Response sample: {'result': True, 'rush_id': '8483934393'}
        """
        
        #Check in db if this tenant has an instanced Rush
        try:
            #Check that rush_name is not empty
            if rush_name is None or len(rush_name) == 0:
                return {'result': False, 'error': 'STARTRUSHEX01', 'error_desc': 'Rush name not provided'}
            
            #Check if type_id exists
            rtc = db_api.rush_type_get(ctxt,rush_type_id)
            if not rtc:
                return {'result': False, 'error': 'STARTRUSHEX02', 'error_desc': 'Rush type does not exist'}
                
            rush_id = uuidutils.generate_uuid()
            
            #Call HEAT to create the stack
            heatcln = heat.heatclient(cfg.CONF.tdaf_username, cfg.CONF.tdaf_user_password, cfg.CONF.tdaf_tenant_name)
            
            #Prapare dict for stack creation
            stack_parms = {
                'KeyName': cfg.CONF.tdaf_instance_key
            }
            
            new_stack_name = cfg.CONF.tdaf_rush_prefix+str(tenant_id)+"-"+str(rush_name)
            
            stack_info = {
                'stack_name': new_stack_name,
                'parameters': stack_parms,
                'template': rtc.template.replace ('\n', '\\n'),
                'timeout_mins': 60,
            }
            heatcln.stacks.create(**stack_info)
        
            stack_list = self.get_stack_list_for_tenant(heatcln,tenant_id)
            if len(stack_list) > 0:
                #Check the name to select the one just created
                for stack in stack_list:
                    stack_info = stack._info;
                    if stack_info['stack_name'] == new_stack_name:
                        break

                if stack_info is not None and stack_info['stack_name'] == new_stack_name:
                    values = {'stack_id':stack_info['id'],'id':rush_id,'rush_type_id':rush_type_id,'status': stack_info['stack_status'], 'name': rush_name}
                    rc = db_api.rush_stack_create(ctxt, values)
                    values = {'rush_id':rush_id,'tenant_id':tenant_id}
                    tc = db_api.rush_tenant_create(ctxt, values)
                    return {'result': True, 'rush_id': rush_id, 'misc': str(stack_info)}
                else:
                    return {'result': False, 'error': 'STARTRUSHEX04', 'error_desc': 'OpenStack stack not found'}
            else:
                return {'result': False, 'error': 'STARTRUSHEX03', 'error_desc': 'OpenStack stack could not be created'}
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
                rt = db_api.rush_tenant_get_by_rush_and_tenant(ctxt, rush_id, tenant_id)
                if not rt or rt.first().tenant_id != tenant_id:
                    return {'result': False, 'error': 'STOPRUSHEX02', 'error_desc': 'Could not find Rush for the tenant'}
                    
                #Call HEAT to destroy the stack
                heatcln = heat.heatclient(cfg.CONF.tdaf_username, cfg.CONF.tdaf_user_password, cfg.CONF.tdaf_tenant_name)
                heatcln.stacks.delete(rsc.stack_id)
                
                rt.delete()
                rsc.delete()
                return {'result': True, 'rush_id': rush_id}
            except Exception as e:
                return {'result': False, 'error': str(e)}
        else:
            return {'result': False, 'error': 'STOPRUSHEX01', 'error_desc': 'Could not find Rush'}

    @request_context
    def get_rush(self, ctxt,tenant_id,rush_id):
        """
        Get the endpoint data for the Rush service identified by rush_id for the tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_id: rush_id to stop
        
        Returns: JSON Specifying the stop result and the rush_id.
        Response sample: {'result': True, 'rush_id': '8483934393', ''ws': 'http://10.95.158.11/rush'}
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
                if rsc.url is None:
                    heatcln = heat.heatclient(cfg.CONF.tdaf_username, cfg.CONF.tdaf_user_password, cfg.CONF.tdaf_tenant_name)
                    self.update_rush_endpointdata(ctxt,heatcln,rsc.stack_id,rush_id)
                    
                return {'result': True, 'rush_id': rush_id, 'url': str(rsc.url)}
            except Exception as e:
                return {'result': False, 'error': str(e)}
        else:
            return {'result': False, 'error': 'GETRUSHEX02', 'error_desc': 'Could not find Rush'}
    
    def get_stack_list_for_tenant(self,heatcln,tenant_id):
        """
        Get all the stacks heat has configured for a tenant

        :param heatcln: HEAT client alread initialized
        :param tenant_id: tenant_id to check
        
        Returns: List of Stack objects with a _info field stating a JSON with the stack data (as defined by HEAT)
        """
        #Build query to get stack id                
        stack_filters = {
            'stack_name': cfg.CONF.tdaf_rush_prefix+str(tenant_id),
        }
        stack_search = {
            'filters': stack_filters,
        }
        stack_generator = heatcln.stacks.list(**stack_search)
        stack_list = []
        for stack in stack_generator:
            stack_list.append(stack)
        return stack_list

    def get_instance_and_ip_list_for_stack_id(self,heatcln,stack_id):
        """
        Get all the instance resources and ip resources configured for a stack_id

        :param heatcln: HEAT client alread initialized
        :param stack_id: stack_id to get all the resources from
        
        Returns: instance_list: list of resource instances found
                 ip_list: list of ip resources found
        """
        #Get the instance list for this stack
        resources = heatcln.resources.list(stack_id)
        instance_list = []
        ip_list = []
        
        for resource in resources:
            res_info = resource._info
            
            #Add those resources that are instances
            if res_info['resource_type'] == 'AWS::EC2::Instance':
                instance_list.append(resource)
            if res_info['resource_type'] == 'AWS::EC2::EIPAssociation':
                ip_list.append(resource)
        return instance_list,ip_list
    
    def update_rush_endpointdata(self,ctxt,heatcln,stack_id,rush_id):
        """
        Updates in the DB the RUSH data based on the stack data

        :param ctxt: RPC context
        :param heatcln: HEAT client alread initialized
        :param stack_id: stack_id to get all the resources from
        :param rush_id: rush_id to be updated with the obtained info
        """
        #Get the instance list for this stack
        instance_list,ip_list = self.get_instance_and_ip_list_for_stack_id(heatcln,stack_id)
        
        #If there is any ip, use it as rush WS
        if len(ip_list)>0:
            ip_info = ip_list[0]._info;
            values = {'url':'http://'+ip_info['physical_resource_id']+':5001'}
            db_api.rush_stack_update(ctxt, rush_id, values)
            
