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
#   This plugin evaluates current latency to write to the test pool.
#
# collectd:
#   http://collectd.org
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml
# ceph pools:
#   https://ceph.com/docs/master/man/8/rados/#pool-specific-commands
#

import collectd
import re
import traceback
import subprocess
import json
import base

class CephLatencyPlugin(base.Base):

    def __init__(self):
        base.Base.__init__(self)
        self.prefix = 'ceph latency'

    def get_stats(self):
        """Retrieves stats regarding latency to write to a test pool"""

        #ceph_cluster = "%s-%s" % (self.prefix, self.cluster)
        ceph_cluster = "."
        data = {
            ceph_cluster: {
		'osd':{},
		},
        }

        output = None
        try:
           # command = "timeout 30s rados --cluster %s -p %s bench 10 write -t 1 -b 65536" % (self.cluster, format(self.testpool))
           output = self.exec_cmd('osd perf') 
          # output = subprocess.check_output(command, shell=True)
        except Exception as exc:
            collectd.error("ceph-latency: failed to run ceph osd perf :: %s :: %s"
                    % (exc, traceback.format_exc()))
            return

        if output is None:
            collectd.error('ceph-latency: failed to run ceph osd perf:: output was None')
	    #collectd.error(output)
        json_data = json.loads(output)
        for osd in json_data['osd_perf_infos']:
            osd_name = ".%s." % osd['id']
            #collectd.error("++++"+osd_name+"++++")
            data[ceph_cluster]['osd'][osd_name] = {}
            data[ceph_cluster]['osd'][osd_name]['commit_latency_ms'] = osd['perf_stats']['commit_latency_ms'] 
            data[ceph_cluster]['osd'][osd_name]['apply_latency_ms'] = osd['perf_stats']['apply_latency_ms'] 
        #regex_match = re.compile('^([a-zA-Z]+) [lL]atency\S+: \s* (\w+.?\w+)\s*', re.MULTILINE)
        #results = regex_match.findall(output)

        #if len(results) == 0:
        #    collectd.error('ceph-latency: failed to run rados bench :: output unrecognized %s' % output)
        #    return

        #data[ceph_cluster]['cluster'] = {}
        #for key, value in results:
         #   if key == 'Average':
         #       data[ceph_cluster]['cluster']['avg_latency'] = float(value) * 1000
#            elif key == 'Stddev':
 #               data[ceph_cluster]['cluster']['stddev_latency'] = float(value) * 1000
 #           elif key == 'Max':
 #               data[ceph_cluster]['cluster']['max_latency'] = float(value) * 1000
 #           elif key == 'Min':
  #              data[ceph_cluster]['cluster']['min_latency'] = float(value) * 1000

        return data

try:
    plugin = CephLatencyPlugin()
except Exception as exc:
    collectd.error("ceph-latency: failed to initialize ceph latency plugin :: %s :: %s"
            % (exc, traceback.format_exc()))

def configure_callback(conf):
    """Received configuration information"""
    plugin.config_callback(conf)
    collectd.register_read(read_callback, plugin.interval)

def read_callback():
    """Callback triggerred by collectd on read"""
    plugin.read_callback()

collectd.register_init(CephLatencyPlugin.reset_sigchld)
collectd.register_config(configure_callback)
