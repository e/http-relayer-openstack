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
SQLAlchemy models for rushstack data.
"""

import sqlalchemy

from sqlalchemy.orm import relationship, backref, object_mapper
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import types
from json import dumps
from json import loads
from rushstack.openstack.common import exception
from rushstack.openstack.common import uuidutils
from rushstack.openstack.common import timeutils
from rushstack.db.sqlalchemy.session import get_session
from sqlalchemy.orm.session import Session

BASE = declarative_base()


class Json(types.TypeDecorator, types.MutableType):
    impl = types.Text

    def process_bind_param(self, value, dialect):
        return dumps(value)

    def process_result_value(self, value, dialect):
        return loads(value)


class RushstackBase(object):
    """Base class for Rushstack Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = sqlalchemy.Column(sqlalchemy.DateTime,
                                   default=timeutils.utcnow)
    updated_at = sqlalchemy.Column(sqlalchemy.DateTime,
                                   onupdate=timeutils.utcnow)

    def save(self, session=None):
        """Save this object."""
        if not session:
            session = Session.object_session(self)
            if not session:
                session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError as e:
            if str(e).endswith('is not unique'):
                raise exception.Duplicate(str(e))
            else:
                raise

    def expire(self, session=None, attrs=None):
        """Expire this object ()."""
        if not session:
            session = Session.object_session(self)
            if not session:
                session = get_session()
        session.expire(self, attrs)

    def refresh(self, session=None, attrs=None):
        """Refresh this object."""
        if not session:
            session = Session.object_session(self)
            if not session:
                session = get_session()
        session.refresh(self, attrs)

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        if not session:
            session = Session.object_session(self)
            if not session:
                session = get_session()
        session.delete(self)
        session.flush()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def update_and_save(self, values, session=None):
        if not session:
            session = Session.object_session(self)
            if not session:
                session = get_session()
        session.begin()
        for k, v in values.iteritems():
            setattr(self, k, v)
        session.commit()

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins.
        """
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()

class RushTenant(BASE, RushstackBase):
    """Represents the relationship between rush id and tenant."""

    __tablename__ = 'rush_tenant'
    rush_id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    tenant_id = sqlalchemy.Column(sqlalchemy.String,primary_key=True)

class RushType(BASE, RushstackBase):
    """Represents the relationship between rush types and template."""

    __tablename__ = 'rush_type'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    template = sqlalchemy.Column(sqlalchemy.Text)

class RushStack(BASE, RushstackBase):
    """Represents the a Rush service instance."""

    __tablename__ = 'rush_stack'
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    stack_id = sqlalchemy.Column(sqlalchemy.String)
    rush_type_id = sqlalchemy.Column(sqlalchemy.Integer)
    status = sqlalchemy.Column(sqlalchemy.String)
    tk = sqlalchemy.Column(sqlalchemy.Text)
    url = sqlalchemy.Column(sqlalchemy.Text)

'''Old Heat classes'''
class RawTemplate(BASE, RushstackBase):
    """Represents an unparsed template which should be in JSON format."""

    __tablename__ = 'raw_template'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    template = sqlalchemy.Column(Json)


class Stack(BASE, RushstackBase):
    """Represents a stack created by the rushstack engine."""

    __tablename__ = 'stack'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True,
                           default=uuidutils.generate_uuid)
    name = sqlalchemy.Column(sqlalchemy.String)
    raw_template_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('raw_template.id'),
        nullable=False)
    raw_template = relationship(RawTemplate, backref=backref('stack'))
    username = sqlalchemy.Column(sqlalchemy.String)
    tenant = sqlalchemy.Column(sqlalchemy.String)
    action = sqlalchemy.Column('action', sqlalchemy.String)
    status = sqlalchemy.Column('status', sqlalchemy.String)
    status_reason = sqlalchemy.Column('status_reason', sqlalchemy.String)
    parameters = sqlalchemy.Column('parameters', Json)
    user_creds_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('user_creds.id'),
        nullable=False)
    owner_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    timeout = sqlalchemy.Column(sqlalchemy.Integer)
    disable_rollback = sqlalchemy.Column(sqlalchemy.Boolean)


class UserCreds(BASE, RushstackBase):
    """
    Represents user credentials and mirrors the 'context'
    handed in by wsgi.
    """

    __tablename__ = 'user_creds'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)
    service_user = sqlalchemy.Column(sqlalchemy.String)
    service_password = sqlalchemy.Column(sqlalchemy.String)
    tenant = sqlalchemy.Column(sqlalchemy.String)
    auth_url = sqlalchemy.Column(sqlalchemy.String)
    aws_auth_url = sqlalchemy.Column(sqlalchemy.String)
    tenant_id = sqlalchemy.Column(sqlalchemy.String)
    aws_creds = sqlalchemy.Column(sqlalchemy.String)
    stack = relationship(Stack, backref=backref('user_creds'))


class Event(BASE, RushstackBase):
    """Represents an event generated by the rushstack engine."""

    __tablename__ = 'event'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    stack_id = sqlalchemy.Column(sqlalchemy.String,
                                 sqlalchemy.ForeignKey('stack.id'),
                                 nullable=False)
    stack = relationship(Stack, backref=backref('events'))

    resource_action = sqlalchemy.Column(sqlalchemy.String)
    resource_status = sqlalchemy.Column(sqlalchemy.String)
    logical_resource_id = sqlalchemy.Column(sqlalchemy.String)
    physical_resource_id = sqlalchemy.Column(sqlalchemy.String)
    resource_status_reason = sqlalchemy.Column(sqlalchemy.String)
    resource_type = sqlalchemy.Column(sqlalchemy.String)
    resource_properties = sqlalchemy.Column(sqlalchemy.PickleType)


class ResourceData(BASE, RushstackBase):
    """Key/value store of arbitrary, resource-specific data."""

    __tablename__ = 'resource_data'

    id = sqlalchemy.Column('id',
                           sqlalchemy.Integer,
                           primary_key=True,
                           nullable=False)
    key = sqlalchemy.Column('key', sqlalchemy.String)
    value = sqlalchemy.Column('value', sqlalchemy.String)
    redact = sqlalchemy.Column('redact', sqlalchemy.Boolean)
    resource_id = sqlalchemy.Column('resource_id',
                                    sqlalchemy.String,
                                    sqlalchemy.ForeignKey('resource.id'),
                                    nullable=False)


class Resource(BASE, RushstackBase):
    """Represents a resource created by the rushstack engine."""

    __tablename__ = 'resource'

    id = sqlalchemy.Column(sqlalchemy.String,
                           primary_key=True,
                           default=uuidutils.generate_uuid)
    action = sqlalchemy.Column('action', sqlalchemy.String)
    status = sqlalchemy.Column('status', sqlalchemy.String)
    name = sqlalchemy.Column('name', sqlalchemy.String, nullable=False)
    nova_instance = sqlalchemy.Column('nova_instance', sqlalchemy.String)
    status_reason = sqlalchemy.Column('status_reason', sqlalchemy.String)
    # odd name as "metadata" is reserved
    rsrc_metadata = sqlalchemy.Column('rsrc_metadata', Json)

    stack_id = sqlalchemy.Column(sqlalchemy.String,
                                 sqlalchemy.ForeignKey('stack.id'),
                                 nullable=False)
    stack = relationship(Stack, backref=backref('resources'))
    data = relationship(ResourceData,
                        cascade="all,delete",
                        backref=backref('resource', lazy='joined'))


class WatchRule(BASE, RushstackBase):
    """Represents a watch_rule created by the rushstack engine."""

    __tablename__ = 'watch_rule'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column('name', sqlalchemy.String, nullable=False)
    rule = sqlalchemy.Column('rule', Json)
    state = sqlalchemy.Column('state', sqlalchemy.String)
    last_evaluated = sqlalchemy.Column(sqlalchemy.DateTime,
                                       default=timeutils.utcnow)

    stack_id = sqlalchemy.Column(sqlalchemy.String,
                                 sqlalchemy.ForeignKey('stack.id'),
                                 nullable=False)
    stack = relationship(Stack, backref=backref('watch_rule'))


class WatchData(BASE, RushstackBase):
    """Represents a watch_data created by the rushstack engine."""

    __tablename__ = 'watch_data'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    data = sqlalchemy.Column('data', Json)

    watch_rule_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('watch_rule.id'),
        nullable=False)
    watch_rule = relationship(WatchRule, backref=backref('watch_data'))
