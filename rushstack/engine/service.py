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

    def get_status(self, ctxt):
        """
        Get Rush service status for the tenant (ctxt should contain tenant_id).

        :param ctxt: RPC context (must contain tenant_id)
        
        Returns: Response got from RPC server.
        Response sample: {'result': True, 'active': True, 'rush_id': '8483934393'}
        """
        #TODO: Do somemething
        logger.debug('request get_status or tenant_id:'+ctxt.tenant_id)
        return {'result': True, 'active': True, 'rush_id': '8483934393'}
