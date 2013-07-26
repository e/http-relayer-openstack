# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012, Red Hat, Inc.
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
Client side of the rushstack engine RPC API.
"""

from rushstack.rpc import api

import rushstack.openstack.common.rpc.proxy


class EngineClient(rushstack.openstack.common.rpc.proxy.RpcProxy):
    '''Client side of the rushstack engine rpc API.

    API version history:

        1.0 - Initial version.
    '''

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self):
        super(EngineClient, self).__init__(
            topic=api.ENGINE_TOPIC,
            default_version=self.BASE_RPC_API_VERSION)

    def echo(self, ctxt, msg):
        """
        The echo method returns same message between '*'.

        :param ctxt: RPC context.
        :param msg: Message to be send to backend
        """
        return self.call(ctxt, self.make_msg('echo',
                                             msg=msg))

    def get_status(self, ctxt, tenant_id):
        """
        Get Rush service status for the tenant (ctxt should contain tenant_id).

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        
        Returns: Response got from RPC server.
        Response sample: {'result': True, 'active': True, 'rush_id': '8483934393'}
        """
        return self.call(ctxt, self.make_msg('get_status',
                                             tenant_id=tenant_id))

    def start_rush_stack(self, ctxt, tenant_id, rush_type_id):
        """
        Instantiate a new Rush service for the required tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id for the new Rush
        :param rush_type_id: rush_type_id for the new rush
        
        Returns: Response got from RPC server.
        Response sample: {'result': True, 'rush_id': '8483934393'}
        """
        return self.call(ctxt, self.make_msg('start_rush_stack',
                                             tenant_id=tenant_id,
                                             rush_type_id=rush_type_id))

    def stop_rush_stack(self, ctxt, tenant_id, rush_id):
        """
        Stop (and destroye) a an existing Rush service for the required tenant

        :param ctxt: RPC context
        :param tenant_id: tenant_id owner of the Rsuh
        :param rush_id: Rush to stop
        
        Returns: Response got from RPC server.
        Response sample: {'result': True}
        """
        return self.call(ctxt, self.make_msg('stop_rush_stack',
                                             tenant_id=tenant_id,
                                             rush_id=rush_id))

    def get_rush_endpoint(self, ctxt, tenant_id, rush_id):
        """
        Get Rush service status for the tenant (ctxt should contain tenant_id).

        :param ctxt: RPC context
        :param tenant_id: tenant_id to check for Rush
        :param rush_id: Rush to get data
        
        Returns: Response got from RPC server.
        Response sample: {'result': True, 'rush_id': '8483934393', 'tk': '77389abbef92e01a0883d', 'ws': 'http://10.95.158.11/rush'}
        """
        return self.call(ctxt, self.make_msg('get_rush_endpoint',
                                             tenant_id=tenant_id,
                                             rush_id=rush_id))
