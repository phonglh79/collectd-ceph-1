#!/usr/bin/env python
#
# vim: tabstop=4 shiftwidth=4

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Ricardo Rocha <ricardo@catalyst.net.nz>
#
# About this plugin:
#   This plugin collects information regarding Ceph pools.
#
# collectd:
#   http://collectd.org
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
# ceph pools:
#   http://ceph.com/docs/master/rados/operations/pools/
#

import collectd
import json
import traceback

import base

class CephPoolPlugin(base.Base):

    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'pool'

    def get_stats(self):
        """Retrieves stats from ceph pools"""

        #ceph_cluster = "." % (self.prefix, self.cluster)
        ceph_cluster = "."
        data = { ceph_cluster: {} }

        stats_output = None
        try:
            stats_output = self.exec_cmd('osd pool stats')
            df_output = self.exec_cmd('df')
        except Exception as exc:
            collectd.error("ceph-pool: failed to ceph pool stats :: %s :: %s"
                    % (exc, traceback.format_exc()))
            return

        json_stats_data = json.loads(stats_output)
        json_df_data = json.loads(df_output)

        # push osd pool stats results
        for pool in json_stats_data:
            pool_key = "pool.gauge-.%s" % pool['pool_name']
            data[ceph_cluster][pool_key] = {}
            pool_data = data[ceph_cluster][pool_key] 
            for stat in ('read_bytes_sec', 'write_bytes_sec', 'op_per_sec', 'write_op_per_sec', 'read_op_per_sec'):
                pool_data[stat] = pool['client_io_rate'][stat] if pool['client_io_rate'].has_key(stat) else 0
            for recover_stat in ('recovering_objects_per_sec', 'recovering_bytes_per_sec', 'recovering_keys_per_sec', 'num_objects_recovered', 'num_bytes_recovered', 'num_keys_recovered'):
                pool_data[recover_stat] = pool['recovery_rate'][recover_stat] if pool['recovery_rate'].has_key(recover_stat) else 0
        # push df results
        for pool in json_df_data['pools']:
            pool_data = data[ceph_cluster]["pool.gauge-.%s" % pool['name']]
            for stat in ('bytes_used', 'kb_used', 'objects', 'max_avail'):
                pool_data[stat] = pool['stats'][stat] if pool['stats'].has_key(stat) else 0

        # push totals from df
        data[ceph_cluster]['cluster'] = {}
        if json_df_data['stats'].has_key('total_bytes'):
            # ceph 0.84+
            data[ceph_cluster]['cluster']['total_space'] = int(json_df_data['stats']['total_bytes'])
            data[ceph_cluster]['cluster']['total_used'] = int(json_df_data['stats']['total_used_bytes'])
            data[ceph_cluster]['cluster']['total_avail'] = int(json_df_data['stats']['total_avail_bytes'])
        else:
            # ceph < 0.84
            data[ceph_cluster]['cluster']['total_space'] = int(json_df_data['stats']['total_space']) * 1024.0
            data[ceph_cluster]['cluster']['total_used'] = int(json_df_data['stats']['total_used']) * 1024.0
            data[ceph_cluster]['cluster']['total_avail'] = int(json_df_data['stats']['total_avail']) * 1024.0

        return data

try:
    plugin = CephPoolPlugin()
except Exception as exc:
    collectd.error("ceph-pool: failed to initialize ceph pool plugin :: %s :: %s"
            % (exc, traceback.format_exc()))

def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)
    collectd.register_read(read_callback, plugin.interval)

def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()

collectd.register_init(CephPoolPlugin.reset_sigchld)
collectd.register_config(configure_callback)
