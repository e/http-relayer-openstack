
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
Routines for configuring Rushstack
"""

import logging as sys_logging
import os

import socket
from oslo.config import cfg

from rushstack.openstack.common import wsgi

from rushstack.openstack.common import log as logging
from rushstack.openstack.common import rpc

DEFAULT_PORT = 18000

paste_deploy_group = cfg.OptGroup('paste_deploy')
paste_deploy_opts = [
    cfg.StrOpt('flavor'),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               help="The API paste config file to use")]


service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='seconds between nodes reporting state to datastore'),
    cfg.IntOpt('periodic_interval',
               default=60,
               help='seconds between running periodic tasks'),
    cfg.StrOpt('instance_connection_is_secure',
               default="0",
               help='Instance connection to cfn/cw API via https'),
    cfg.StrOpt('instance_connection_https_validate_certificates',
               default="1",
               help='Instance connection to cfn/cw API validate certs if ssl'),
    cfg.StrOpt('rushstack_stack_user_role',
               default="rushstack_stack_user",
               help='Keystone role for rushstack template-defined users')]

db_opts = [
    cfg.StrOpt('sql_connection',
               default='mysql://rushstack:rushstack@localhost/rushstack',
               help='The SQLAlchemy connection string used to connect to the '
               'database'),
    cfg.IntOpt('sql_idle_timeout',
               default=3600,
               help='timeout before idle sql connections are reaped')]

engine_opts = [
    cfg.StrOpt('auth_uri',
               default='http://localhost:35357/v2.0',
               help='The default auth_uri to keystone'),
    cfg.StrOpt('tdaf_username',
               default='tdafsrv',
               help='User to connect to keystone and heat'),
    cfg.StrOpt('tdaf_user_password',
               default='tdafsrvpwd',
               help='Password of the tdaf_username'),
    cfg.StrOpt('orchestration_type',
               default='orchestration',
               help='Type of services to request orchestration from keystone'),
    cfg.StrOpt('tdaf_tenant_name',
               default='TDAFServices',
               help='Tenant name in which service instances will be created'),
    cfg.StrOpt('tdaf_rush_prefix',
               default='RUSH-',
               help='Prefix for naming the stacks for RUSH'),
    cfg.StrOpt('tdaf_instance_key',
                default='TDAF',
                help='SSH public key to use when creating the instances'),
    cfg.ListOpt('plugin_dirs',
                default=['/usr/lib64/rushstack', '/usr/lib/rushstack'],
                help='List of directories to search for Plugins')]

rpc_opts = [
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of the engine node. '
                    'This can be an opaque identifier.'
                    'It is not necessarily a hostname, FQDN, or IP address.')]

cfg.CONF.register_opts(db_opts)
cfg.CONF.register_opts(engine_opts)
cfg.CONF.register_opts(service_opts)
cfg.CONF.register_opts(rpc_opts)
cfg.CONF.register_group(paste_deploy_group)
cfg.CONF.register_opts(paste_deploy_opts, group=paste_deploy_group)

# TODO(jianingy): I'll set allowed_rpc_exception_modules here for now.
#                 after figure out why rpc_set_default was not called,
#                 I'll move these settings into rpc_set_default()
allowed_rpc_exception_modules = cfg.CONF.allowed_rpc_exception_modules
allowed_rpc_exception_modules.append('rushstack.common.exception')
cfg.CONF.set_default(name='allowed_rpc_exception_modules',
                     default=allowed_rpc_exception_modules)


def rpc_set_default():
    rpc.set_defaults(control_exchange='rushstack')


def _get_deployment_flavor():
    """
    Retrieve the paste_deploy.flavor config item, formatted appropriately
    for appending to the application name.
    """
    flavor = cfg.CONF.paste_deploy.flavor
    return '' if not flavor else ('-' + flavor)


def _get_deployment_config_file():
    """
    Retrieve the deployment_config_file config item, formatted as an
    absolute pathname.
    """
    config_path = cfg.CONF.find_file(
        cfg.CONF.paste_deploy['api_paste_config'])
    if config_path is None:
        return None

    return os.path.abspath(config_path)


def load_paste_app(app_name=None):
    """
    Builds and returns a WSGI app from a paste config file.

    We assume the last config file specified in the supplied ConfigOpts
    object is the paste config file.

    :param app_name: name of the application to load

    :raises RuntimeError when config file cannot be located or application
            cannot be loaded from config file
    """
    if app_name is None:
        app_name = cfg.CONF.prog

    # append the deployment flavor to the application name,
    # in order to identify the appropriate paste pipeline
    app_name += _get_deployment_flavor()

    conf_file = _get_deployment_config_file()
    if conf_file is None:
        raise RuntimeError("Unable to locate config file")

    try:
        app = wsgi.paste_deploy_app(conf_file, app_name, cfg.CONF)

        # Log the options used when starting if we're in debug mode...
        if cfg.CONF.debug:
            cfg.CONF.log_opt_values(logging.getLogger(app_name),
                                    sys_logging.DEBUG)

        return app
    except (LookupError, ImportError) as e:
        raise RuntimeError("Unable to load %(app_name)s from "
                           "configuration file %(conf_file)s."
                           "\nGot: %(e)r" % locals())
