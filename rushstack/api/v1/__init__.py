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

import routes

from rushstack.openstack.common import gettextutils

gettextutils.install('rushstack')

from rushstack.api.v1 import rush
from rushstack.openstack.common import wsgi

from rushstack.openstack.common import log as logging

logger = logging.getLogger(__name__)


class API(wsgi.Router):

    """
    WSGI router for Rushstack v1 ReST API requests.
    """

    def __init__(self, conf, **local_conf):
        self.conf = conf
        mapper = routes.Mapper()

        # Actions
        rush_path = "/{tenant_id}/rushes"
        actions_resource = rush.create_resource(conf)
        with mapper.submapper(controller=actions_resource,
                              path_prefix=rush_path) as ac_mapper:

            # Rush methods handling
            #Test method
            ac_mapper.connect("echo",
                                 "/echo",
                                 action="echo",
                                 conditions={'method': 'GET'})

            ac_mapper.connect("list",
                                 "",
                                 action="get_list",
                                 conditions={'method': 'GET'})

            ac_mapper.connect("create",
                                 "",
                                 action="create_rush",
                                 conditions={'method': 'PUT'})

            ac_mapper.connect("delete",
                                 "/{rush_id}",
                                 action="delete_rush",
                                 conditions={'method': 'DELETE'})

            ac_mapper.connect("get_rush",
                                 "/{rush_id}",
                                 action="get_rush",
                                 conditions={'method': 'GET'})

        super(API, self).__init__(mapper)
