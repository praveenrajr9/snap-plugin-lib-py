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
import datetime
#import example111
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

class IOSnoopStats:



    trace_file_path = '/sys/kernel/debug/tracing/trace'
    rq_complete_enable_path = '/sys/kernel/debug/tracing/events/block/block_rq_complete/enable'
    rq_issue_enable_path = "/sys/kernel/debug/tracing/events/block/block_rq_issue/enable"
    def __init__(self):
        
        self.metric_list = {}
        self.starts = {}
        self.comms = {}
	self.pids = {}
	self.action_type = {}
	self.nsectors = {}
        self.disable_event = 0
   
    def enable_tracing(self):
        rq_complete_enable = open(self.rq_issue_enable_path,"w")
        rq_issue_enable = open(self.rq_complete_enable_path,"w")
        rq_complete_enable.seek(0)
        rq_issue_enable.seek(0)
        rq_complete_enable.write("1")
        rq_issue_enable.write("1")
        rq_complete_enable.close()
        rq_issue_enable.close()

    def disable_tracing(self):
        rq_complete_enable = open(self.rq_issue_enable_path,"w")
        rq_issue_enable = open(self.rq_complete_enable_path,"w")

        rq_complete_enable.seek(0)
        rq_issue_enable.seek(0)

        rq_complete_enable.write("0")
        rq_issue_enable.write("0")
        file_wrt = open(self.trace_file_path,"w")
        file_wrt.write("")
        file_wrt.close()
        rq_complete_enable.close()
        rq_issue_enable.close()

        
     
        
 
    def restart_tracing(self):
        self.disable_tracing()      
        self.enable_tracing() 

    def collect_tracing(self):
        self.metric_list = []
        starts = {}
        comms = {}
        pids = {}

        with open(self.trace_file_path,"r") as f:
            for line in (l for l in f if l != ""):
                if '#' not in line:
#['<idle>-0', '[005]', 'd.s.', '365147.088940:', 'block_rq_complete:', '8,0', 'WS', '()', '471135552', '+', '0', '[0]']

                    line_list = line.split()
                    line_len = len(line_list)
                    time_t = line_list[3]
                    time_t = float(time_t.split(":")[0])
                    comm_pid = line_list[0]
                    comm_pid = comm_pid.split("-")
                    pid = comm_pid[len(comm_pid)-1]
                    comm_name = '-'.join(comm_pid[0:len(comm_pid)-1])
                    dev = line_list[5]
                    if 'issue' in line:
                        sector_loc = line_list[line_len - 4]
                        starts[sector_loc + dev] = time_t
                        comms[sector_loc + dev] = comm_name
                        pids[sector_loc + dev] = pid

                    if 'complete' in line:
                        stats = {}
                        action_type = line_list[line_len - 6]
                        sector_loc = line_list[line_len - 4]
                        nsectors = int(line_list[line_len - 2])
                        try:
                            comm = comms[sector_loc + dev]
                            pid = pids[sector_loc + dev]
                            latency = 1000 * (time_t - starts[sector_loc + dev])
                            ends = time_t
                            nsectors = nsectors * 512
                      
                            stats['command'] = comm
                            stats['pid'] = pid
                            stats['latency'] = latency
                            stats['start'] = starts[sector_loc + dev]
                            stats['end'] = ends
                            stats['type'] = action_type
                            stats['dev'] = dev
                            stats['block'] = sector_loc
                            stats['bytes'] = nsectors 
                            stats['lat'] = latency
                            self.metric_list.append(stats)    
                        except Exception as e:
                            continue
	return self.metric_list



class CollectorIOSnoopStats(snap.Collector):
    def __init__(self):
        self.disable_event = 0
        self.iosnoop_stats = IOSnoopStats()
        super(self.__class__, self).__init__("collector-iosnoop-metrics-py", 1, concurrency_count=1,  routing_strategy=1)
 
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names = ['start', 'end', 'command', 'pid', 'type', 'dev', 
                        'block', 'bytes', 'lat']
                         
        for key in metric_names:
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="sys"),
                    snap.NamespaceElement(value="kernel"),
                    snap.NamespaceElement(value="block_trace"),
                    snap.NamespaceElement("pid","pid of process"),
                    snap.NamespaceElement(value=key)
                ],
                version=1,
                
            )
            metrics.append(metric)
        return metrics


    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
        LOG.info("CollectMetrics called")
        if self.disable_event == 0:
            self.iosnoop_stats.enable_tracing()
            self.disable_event = 1
            return metrics
        else:
            new_metrics = [] 
            metric_list = self.iosnoop_stats.collect_tracing()
            self.iosnoop_stats.restart_tracing()
            for stats in metric_list:
                pids = stats['pid']
                for metric in metrics:
                    typ = metric.namespace[4].value
                    if typ == '*':
                        new_metric = snap.Metric(version=1, Description="iosnoop metrics")
                        new_metric.namespace.add_static_element("intel")
                        new_metric.namespace.add_static_element("sys")
                        new_metric.namespace.add_static_element("kernel")
                        new_metric.namespace.add_static_element("block_trace")
                        new_metric.namespace.add_static_element(pids)
                        new_metric.namespace.add_static_element(metric.namespace[5].value)
                        new_metric.data = stats[metric.namespace[5].value]
                        new_metric.timestamp = time.time()
                        new_metrics.append(new_metric)



        return new_metrics



    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()

    def iosnoop_cleanup(self):
        rq_complete_enable = open("/home/praveenraj/snap-plugin-lib-py/examples/collector/snap_temp.txt","w")
        rq_complete_enable.write("hhhhhhhhhhhhhhhh")
 
        self.iosnoop_stats.disable_tracing() 


if __name__ == "__main__":

     collector_iosnoop = CollectorIOSnoopStats()
     collector_iosnoop.start_plugin()
     rq_complete_enable = open("/home/praveenraj/snap_temp.txt","w")
    # rq_issue_enable = open(self.rq_complete_enable_path,"w")

    # rq_issue_enable.seek(0)

    # rq_issue_enable.write("0")

     collector_iosnoop.iosnoop_cleanup()     
   # CollectorIOSnoopStats().start_plugin()
   # ollectorIOSnoopStats()
