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
from rushstack.api.v1 import actions
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

        rush_resource = rush.create_resource(conf)

        with mapper.submapper(controller=rush_resource,
                              path_prefix="/{tenant_id}") as rush_mapper:
            # Template handling
            rush_mapper.connect("template_validate",
                                 "/validate",
                                 action="validate_template",
                                 conditions={'method': 'POST'})
            rush_mapper.connect("resource_types",
                                 "/resource_types",
                                 action="list_resource_types",
                                 conditions={'method': 'GET'})

            # Stack collection
            rush_mapper.connect("stack_index",
                                 "/stacks",
                                 action="index",
                                 conditions={'method': 'GET'})
            rush_mapper.connect("stack_create",
                                 "/stacks",
                                 action="create",
                                 conditions={'method': 'POST'})
            rush_mapper.connect("stack_detail",
                                 "/stacks/detail",
                                 action="detail",
                                 conditions={'method': 'GET'})

            # Stack data
            rush_mapper.connect("stack_lookup",
                                 "/stacks/{stack_name}",
                                 action="lookup")
            # \x3A matches on a colon.
            # Routes treats : specially in its regexp
            rush_mapper.connect("stack_lookup",
                                 r"/stacks/{stack_name:arn\x3A.*}",
                                 action="lookup")
            subpaths = ['resources', 'events', 'template', 'actions']
            path = "{path:%s}" % '|'.join(subpaths)
            rush_mapper.connect("stack_lookup_subpath",
                                 "/stacks/{stack_name}/" + path,
                                 action="lookup",
                                 conditions={'method': 'GET'})
            rush_mapper.connect("stack_lookup_subpath_post",
                                 "/stacks/{stack_name}/" + path,
                                 action="lookup",
                                 conditions={'method': 'POST'})
            rush_mapper.connect("stack_show",
                                 "/stacks/{stack_name}/{stack_id}",
                                 action="show",
                                 conditions={'method': 'GET'})
            rush_mapper.connect("stack_template",
                                 "/stacks/{stack_name}/{stack_id}/template",
                                 action="template",
                                 conditions={'method': 'GET'})

            # Stack update/delete
            rush_mapper.connect("stack_update",
                                 "/stacks/{stack_name}/{stack_id}",
                                 action="update",
                                 conditions={'method': 'PUT'})
            rush_mapper.connect("stack_delete",
                                 "/stacks/{stack_name}/{stack_id}",
                                 action="delete",
                                 conditions={'method': 'DELETE'})

        # Actions
        rush_path = "/{tenant_id}/rush/{stack_name}/{stack_id}"
        actions_resource = actions.create_resource(conf)
        with mapper.submapper(controller=actions_resource,
                              path_prefix=rush_path) as ac_mapper:

            ac_mapper.connect("action_stack",
                              "/actions",
                              action="action",
                              conditions={'method': 'POST'})

        super(API, self).__init__(mapper)
