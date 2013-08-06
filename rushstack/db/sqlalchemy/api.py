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

'''Implementation of SQLAlchemy backend.'''
from sqlalchemy.orm.session import Session

from rushstack.common import crypt
from rushstack.openstack.common import exception
from rushstack.db.sqlalchemy import models
from rushstack.db.sqlalchemy.session import get_session


def model_query(context, *args):
    session = _session(context)
    query = session.query(*args)

    return query


def _session(context):
    return (context and context.session) or get_session()

def rush_tenant_get_all_by_tenant(context, tenant_id):
    result = model_query(context, models.RushTenant).\
        filter_by(tenant_id=tenant_id)

    return result

def rush_stack_create(context, values):
    rush_stack_ref = models.RushStack()
    rush_stack_ref.update(values)
    rush_stack_ref.save(_session(context))
    return rush_stack_ref

def rush_tenant_create(context, values):
    rush_tenant_ref = models.RushTenant()
    rush_tenant_ref.update(values)
    rush_tenant_ref.save(_session(context))
    return rush_tenant_ref

def rush_type_get(context, type_id):
    return model_query(context, models.RushType).get(type_id)

def rush_stack_get(context, rush_id):
    return model_query(context, models.RushStack).get(rush_id)

def rush_stack_update(context, rush_id, values):
    rushstack = rush_stack_get(context, rush_id)

    if not rushstack:
        raise exception.NotFound('Attempt to update a rushstack with id: %s %s' %
                                 (rush_id, 'that does not exist'))

    rushstack.update(values)
    rushstack.save(_session(context))
