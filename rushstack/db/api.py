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


def rush_tenant_get_all_by_tenant(context, tenant_id):
    return IMPL.rush_tenant_get_all_by_tenant(context, tenant_id)

def rush_tenant_create(context, values):
    return IMPL.rush_tenant_create(context, values)

def rush_stack_create(context, values):
    return IMPL.rush_stack_create(context, values)

def rush_type_get(context, type_id):
    return IMPL.rush_type_get(context, type_id)

def rush_stack_get(context, rush_id):
    return IMPL.rush_stack_get(context, rush_id)

def rush_stack_update(context, rush_id, values):
    return IMPL.rush_stack_update(context, rush_id, values)
