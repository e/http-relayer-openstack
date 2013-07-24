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

'''
Interface for database access.

Usage:

    >>> from rushstack import db
    >>> db.event_get(context, event_id)
    # Event object received

The underlying driver is loaded . SQLAlchemy is currently the only
supported backend.
'''

from oslo.config import cfg

from rushstack.db import utils

SQL_CONNECTION = 'sqlite://'
SQL_IDLE_TIMEOUT = 3600
db_opts = [
    cfg.StrOpt('db_backend',
               default='sqlalchemy',
               help='The backend to use for db')]

cfg.CONF.register_opts(db_opts)

IMPL = utils.LazyPluggable('db_backend',
                           sqlalchemy='rushstack.db.sqlalchemy.api')


cfg.CONF.import_opt('sql_connection', 'rushstack.openstack.common.config')
cfg.CONF.import_opt('sql_idle_timeout', 'rushstack.openstack.common.config')


def configure():
    global SQL_CONNECTION
    global SQL_IDLE_TIMEOUT
    SQL_CONNECTION = cfg.CONF.sql_connection
    SQL_IDLE_TIMEOUT = cfg.CONF.sql_idle_timeout


def get_session():
    return IMPL.get_session()


def raw_template_get(context, template_id):
    return IMPL.raw_template_get(context, template_id)


def raw_template_get_all(context):
    return IMPL.raw_template_get_all(context)


def raw_template_create(context, values):
    return IMPL.raw_template_create(context, values)


def resource_data_get(resource, key):
    return IMPL.resource_data_get(resource, key)


def resource_data_set(resource, key, value, redact=False):
    return IMPL.resource_data_set(resource, key, value, redact=redact)


def resource_data_get_by_key(context, resource_id, key):
    return IMPL.resource_data_get_by_key(context, resource_id, key)


def resource_get(context, resource_id):
    return IMPL.resource_get(context, resource_id)


def resource_get_all(context):
    return IMPL.resource_get_all(context)


def resource_create(context, values):
    return IMPL.resource_create(context, values)


def resource_get_all_by_stack(context, stack_id):
    return IMPL.resource_get_all_by_stack(context, stack_id)


def resource_get_by_name_and_stack(context, resource_name, stack_id):
    return IMPL.resource_get_by_name_and_stack(context,
                                               resource_name, stack_id)


def resource_get_by_physical_resource_id(context, physical_resource_id):
    return IMPL.resource_get_by_physical_resource_id(context,
                                                     physical_resource_id)


def stack_get(context, stack_id, admin=False):
    return IMPL.stack_get(context, stack_id, admin)


def stack_get_by_name(context, stack_name):
    return IMPL.stack_get_by_name(context, stack_name)


def stack_get_all(context):
    return IMPL.stack_get_all(context)


def stack_get_all_by_tenant(context):
    return IMPL.stack_get_all_by_tenant(context)


def stack_create(context, values):
    return IMPL.stack_create(context, values)


def stack_update(context, stack_id, values):
    return IMPL.stack_update(context, stack_id, values)


def stack_delete(context, stack_id):
    return IMPL.stack_delete(context, stack_id)


def user_creds_create(context):
    return IMPL.user_creds_create(context)


def user_creds_get(context_id):
    return IMPL.user_creds_get(context_id)


def event_get(context, event_id):
    return IMPL.event_get(context, event_id)


def event_get_all(context):
    return IMPL.event_get_all(context)


def event_get_all_by_tenant(context):
    return IMPL.event_get_all_by_tenant(context)


def event_get_all_by_stack(context, stack_id):
    return IMPL.event_get_all_by_stack(context, stack_id)


def event_create(context, values):
    return IMPL.event_create(context, values)


def watch_rule_get(context, watch_rule_id):
    return IMPL.watch_rule_get(context, watch_rule_id)


def watch_rule_get_by_name(context, watch_rule_name):
    return IMPL.watch_rule_get_by_name(context, watch_rule_name)


def watch_rule_get_all(context):
    return IMPL.watch_rule_get_all(context)


def watch_rule_get_all_by_stack(context, stack_id):
    return IMPL.watch_rule_get_all_by_stack(context, stack_id)


def watch_rule_create(context, values):
    return IMPL.watch_rule_create(context, values)


def watch_rule_update(context, watch_id, values):
    return IMPL.watch_rule_update(context, watch_id, values)


def watch_rule_delete(context, watch_id):
    return IMPL.watch_rule_delete(context, watch_id)


def watch_data_create(context, values):
    return IMPL.watch_data_create(context, values)


def watch_data_get_all(context):
    return IMPL.watch_data_get_all(context)


def watch_data_delete(context, watch_name):
    return IMPL.watch_data_delete(context, watch_name)
