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
#   This plugin collects information regarding Ceph OSDs.
#
# collectd:
#   http://collectd.org
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
# ceph osds:
#   http://ceph.com/docs/master/rados/operations/monitoring/#checking-osd-status
#

import collectd
import json
import traceback
import base

class CephOsdPlugin(base.Base):

    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'osd'

    def get_stats(self):
        """Retrieves stats from ceph osds"""

        #ceph_cluster = "%s-%s" % (self.prefix, self.cluster)
        ceph_cluster = "."
        data = { ceph_cluster: { 
            'pool': {},
            'osd': {},
            'osd_4.': { 'up': 0, 'in': 0, 'down': 0, 'out': 0} 
        } }
        output = self.exec_cmd('osd dump')
        if output is None:
            return

        json_data = json.loads(output)

        # number of pools
        #data[ceph_cluster]['pool']['number'] = len(json_data['pools'])

        # pool metadata
        for pool in json_data['pools']:
            pool_name = ".%s." % pool['pool_name']
            data[ceph_cluster]['pool'][pool_name] = {}
            data[ceph_cluster]['pool'][pool_name]['size'] = pool['size']
            data[ceph_cluster]['pool'][pool_name]['min_size'] = pool['min_size']
            data[ceph_cluster]['pool'][pool_name]['pg_num'] = pool['pg_num']
            data[ceph_cluster]['pool'][pool_name]['pgp_num'] = pool['pg_placement_num']
            data[ceph_cluster]['pool'][pool_name]['id'] = pool['pool']

        osd_data = data[ceph_cluster]['osd_4.']
        # number of osds in each possible state
        for osd in json_data['osds']:
            osd_name = ".%s." % osd['osd']
            data[ceph_cluster]['osd'][osd_name] = {}
            data[ceph_cluster]['osd'][osd_name]['id'] = osd['osd']
            data[ceph_cluster]['osd'][osd_name]['weight'] = osd['weight']
            data[ceph_cluster]['osd'][osd_name]['up_from'] = osd['up_from']
            data[ceph_cluster]['osd'][osd_name]['up_thru'] = osd['up_thru']
            data[ceph_cluster]['osd'][osd_name]['down_at'] = osd['down_at']
            if osd['up'] == 1:
                osd_data['up'] += 1
            else:
                osd_data['down'] += 1
            if osd['in'] == 1:
                osd_data['in'] += 1
            else:
                osd_data['out'] += 1

        output = self.exec_cmd('osd df')
        if output is None:
	    return
	json_data = json.loads(output)
	for osd in json_data['nodes']:
	    osd_name = ".%s." % osd['id']
	    data[ceph_cluster]['osd'][osd_name]['utilization'] = osd['utilization']
	    data[ceph_cluster]['osd'][osd_name]['kb_used'] = osd['kb_used']
	    data[ceph_cluster]['osd'][osd_name]['kb_avail'] = osd['kb_avail']
	    data[ceph_cluster]['osd'][osd_name]['var'] = osd['var']

        return data

try:
    plugin = CephOsdPlugin()
except Exception as exc:
    collectd.error("ceph-osd: failed to initialize ceph osd plugin :: %s :: %s"
            % (exc, traceback.format_exc()))

def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)
    collectd.register_read(read_callback, plugin.interval)

def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()

def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)
    collectd.register_read(read_callback, plugin.interval)

collectd.register_config(configure_callback)
