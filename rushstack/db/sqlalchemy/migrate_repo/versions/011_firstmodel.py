# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import sqlalchemy


def upgrade(migrate_engine):
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine

    rush_type = sqlalchemy.Table(
        'rush_type', meta,
        sqlalchemy.Column('id', sqlalchemy.Integer,
                          primary_key=True, nullable=False),
        sqlalchemy.Column('name', sqlalchemy.String(126)),
        sqlalchemy.Column('template', sqlalchemy.Text),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
    )

    rush_stack = sqlalchemy.Table(
        'rush_stack', meta,
        sqlalchemy.Column('id', sqlalchemy.String(36),
                          primary_key=True, nullable=False),
        sqlalchemy.Column('name', sqlalchemy.String(126)),
        sqlalchemy.Column('stack_id', sqlalchemy.String(36), nullable=False),
        sqlalchemy.Column('rush_type_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('rush_type.id'), nullable=False),
        sqlalchemy.Column('status', sqlalchemy.String(36), nullable=False),
        sqlalchemy.Column('extdata', sqlalchemy.Text),
        sqlalchemy.Column('url', sqlalchemy.Text),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
    )

    rush_tenant = sqlalchemy.Table(
        'rush_tenant', meta,
        sqlalchemy.Column('rush_id', sqlalchemy.String(36), sqlalchemy.ForeignKey('rush_stack.id'),
                          primary_key=True, nullable=False),
        sqlalchemy.Column('tenant_id', sqlalchemy.String(64),
                          primary_key=True, nullable=False),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
    )

    rush_instance = sqlalchemy.Table(
        'rush_instance', meta,
        sqlalchemy.Column('instance_id', sqlalchemy.String(255),
                          primary_key=True, nullable=False),
        sqlalchemy.Column('rush_id', sqlalchemy.String(36),
                          primary_key=True, nullable=False),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime),
    )

    tables = (
        rush_type,
        rush_stack,
        rush_tenant,
        rush_instance,
    )

    for index, table in enumerate(tables):
        try:
            table.create()
        except:
            # If an error occurs, drop all tables created so far to return
            # to the previously existing state.
            meta.drop_all(tables=tables[:index])
            raise


def downgrade(migrate_engine):
    raise Exception('Database downgrade not supported - would drop all tables')
