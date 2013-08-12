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
    name = sqlalchemy.Column(sqlalchemy.String)
    stack_id = sqlalchemy.Column(sqlalchemy.String)
    rush_type_id = sqlalchemy.Column(sqlalchemy.Integer)
    status = sqlalchemy.Column(sqlalchemy.String)
    extdata = sqlalchemy.Column(sqlalchemy.Text)
    url = sqlalchemy.Column(sqlalchemy.Text)
