#!/usr/bin/env python

# http://www.apache.org/licenses/LICENSE-2.0.txt
#
# Copyright 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import random
import time
#import example111
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

class VMPageStats:

    # http://lxr.osuosl.org/source/Documentation/iostats.txt
    #vmstat_metrics = ['pgpgin', 'pgpgout', 'pgfault', 'pgmajfault', 'pgfree',
    #                  'pgsteal', 'pgscan_kswapd', 'pgscan_direct']


    file_path = '/proc/vmstat'
    def __init__(self, duration=1):
        self.interval = duration
        self.previous_stats = {}
        self.current_stats = {}
        self.devices = []
        self.metric_list = {}

    def read_vmstats(self):
        pg_steal = pgscan_kswapd = pgscan_direct = 0.00
        result = {}
        with open(self.file_path, 'r') as f:
            for line in (l for l in f  if l != ''):
                line_list = line.split(' ')
                if 'pgpgin' in line_list[0]:
                    result['pgpgin'] = int(line_list[1])
                if 'pgpgout' in line_list[0]:
                    result['pgpgout'] = int(line_list[1])
                if 'pgfault' in line_list[0]:
                    result['pgfault'] = int(line_list[1])
                if 'pgmajfault' in line_list[0]:
                    result['pgmajfault'] = int(line_list[1])
                if 'pgfree' in line_list[0]:
                    result['pgfree'] = int(line_list[1])
                if 'pgsteal_' in line_list[0]:
                    pg_steal = int(line_list[1])
                if 'pgscan_kswapd' in line_list[0]:
                    pgscan_kswapd = int(line_list[1])
                if 'pgscan_direct' in line_list[0]:
                    pgscan_direct = int(line_list[1])
        result['pgsteal'] = pg_steal
        result['pgscan_kswapd'] = pgscan_kswapd
        result['pgscan_direct'] = pgscan_direct

        return result


    def calculate_diff(self):
        
        metric_list = {}
        metric_list['vmeff%'] = 0.0
        metric_list['pgpgin_per_itv'] = self.current_stats['pgpgin'] - self.previous_stats['pgpgin']
        metric_list['pgpgout_per_itv'] = self.current_stats['pgpgout'] - self.previous_stats['pgpgout']
        metric_list['pgfault_per_itv'] = self.current_stats['pgfault'] - self.previous_stats['pgfault']
        metric_list['pgmajfault_per_itv'] = self.current_stats['pgmajfault'] - self.previous_stats['pgmajfault']
        metric_list['pgfree_per_itv'] = self.current_stats['pgfree'] - self.previous_stats['pgfree']
        metric_list['pgsteal_per_itv'] = self.current_stats['pgsteal'] - self.previous_stats['pgsteal']
        metric_list['pgscan_kswapd_per_itv'] = self.current_stats['pgscan_kswapd'] - self.previous_stats['pgscan_kswapd']
        metric_list['pgscan_direct_per_itv'] = self.current_stats['pgscan_direct'] - self.previous_stats['pgscan_direct']
        curr_total_page_scan = self.current_stats['pgscan_kswapd'] + self.current_stats['pgscan_direct']
        prev_total_page_scan = self.previous_stats['pgscan_kswapd'] + self.previous_stats['pgscan_direct']
        diff_total_pg_scan = curr_total_page_scan - prev_total_page_scan
        if (diff_total_pg_scan != 0):
            metric_list['vmeff%'] = metric_list['pgsteal_per_itv'] / diff_total_pg_scan * 100
        self.metric_list = metric_list
        return self.metric_list



class SarVMStats(snap.Collector):
    def __init__(self):
        self.vm_stats = VMPageStats(1)
        self.vm_stats.current_stats = self.vm_stats.read_vmstats()
        super(self.__class__, self).__init__("collector-sar-vmstats-metrics-py", 1)
 
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names = ['pgpgin_per_itv', 'pgpgout_per_itv', 'pgfault_per_itv',
                        'pgfree_per_itv', 'pgsteal_per_itv', 'pgscan_kswapd_per_itv',
			'pgscan_direct_per_itv', 'vmeff%']
                         
        for key in metric_names:
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="vmstats"),
                    snap.NamespaceElement(value=key)
                ],
                version=1,
                
            )
            metrics.append(metric)
        return metrics


    def collect(self, metrics):
        LOG.debug("CollectMetrics called")

        fs = open("/sys/kernel/debug/tracing/events/block/block_rq_complete/enable","w")
        fs.seek(0)
        fs.write("1")
        self.vm_stats.previous_stats = self.vm_stats.current_stats
        self.vm_stats.current_stats = self.vm_stats.read_vmstats()
        time.sleep(2)
        metric_list = self.vm_stats.calculate_diff()
        for metric in metrics:
            metric_name = metric.namespace[2].value           
            metric.data = metric_list[metric_name]
            metric.timestamp = time.time()
        return metrics


    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":

    SarVMStats().start_plugin()
