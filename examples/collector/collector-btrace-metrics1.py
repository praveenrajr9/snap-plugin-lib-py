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
import subprocess as sub
import time
import re
#import example111
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

class IOBtraceStats:
    def __init__(self):
        self.per_proc_stats_list = []
        self.throughput_stats = {}
        
    def parse_metrics(self, result):
        i=0
        while i < range(len(result)-1):
            try:
                temp_list = result[i].split()
       	        len_temp_list = len(temp_list)
                if len_temp_list == 2 and len_temp_list != 0:
                    fill_per_proc_data(result, i, temp_list[0])
                    i = i + 8
                    continue
                if len_temp_list == 5 and len_temp_list != 0:
       #             self.throughput_stats = fill_throughput_data(result, i)
                    break
                i = i + 1
            except Exception as e:
               LOG.debug(e)
        #return self.per_proc_stats_list

     
    def fill_per_proc_data(self, result, i, proc_num):
        per_proc_stats = {}
        stats = {}
        try:
            for k in range(i+1,i+8):
                temp_list = result[k].split("\t")
                for val in temp_list:

                    
                    val = val.split(":")
                    if len(val) == 1:
                       continue

                    temp_key = val[0].strip()
                    temp_val = val[1].split(",")
                    

                    stats[temp_key] = int(temp_val[0].strip())
                    if (len(temp_val) == 2):
                        temp_val[1] = re.split("(\d+)",temp_val[1])[1]
                        
                        stats[temp_key +" KiB"] = int(temp_val[1].strip())

                    
        except Exception as e:
            LOG.debug(e)
        per_proc_stats[proc_num] = stats
        self.per_proc_stats_list.append(per_proc_stats)

    def fill_throughput_data(result, i):
        stats = {}
        throughput = result[i].split(":")
        read_writes = throughput[1].split(" / ")
        stats[throughput[0]] = read_writes

        events = result[i+1].split(":")
        stats[events[0]] = events[1]

         
        return stats
    



class CollectorBtraceStats(snap.Collector):
    def __init__(self):
        self.disable_event = 0
        #self.files = open("/home/praveenraj/btrace1.txt","w")
        self.btrace_stats = IOBtraceStats()
        super(self.__class__, self).__init__("collector-btrace-metrics-py", 1)
         
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names =  ['Reads Queued','Reads Queued KiB', 'Read Dispatches',
                        'Read Dispatches KiB', 'Reads Requeued', 'Reads Completed', 
                        'Reads Completed KiB', 'Read Merges', 'Read Merges KiB',
                        'Read Depth', 'Writes Queued', 'Writes Queued KiB', 
                        'Write Dispatches', 'Write Dispatches KiB', 'Writes Requeued',
                        'Writes Completed','Writes Completed KiB', 'Write Merges', 
                        'Write Merges KiB', 'Write Depth', 'IO unplugs', 'Timer unplugs' ]
 
                         
        for key in metric_names:
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="btrace"),
                    snap.NamespaceElement("pid","pid of process"), # dynamic element
                    snap.NamespaceElement(value=key)
                ],
                version=1,
                
            )
            metrics.append(metric)
        return metrics
    
    def collect_metrics(self):
        self.result = self.proc.communicate()
        self.proc = sub.Popen(["btrace","-s","-t","-w","5","/dev/sda"],stdout=sub.PIPE)
        self.result = self.result[0].split("\n")
        self.btrace_stats.parse_metrics(self.result)
        return "collected_metrics"

        
  
    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
       
       # self.files.write("proc_name")
        if self.disable_event == 0:
           self.disable_event = 1
           self.proc = sub.Popen(["btrace","-s","-t","-w","5","/dev/sda"],stdout=sub.PIPE)
            
           return metrics
        else:
           metric_list = self.collect_metrics()
            
        new_metrics = []
        new_metric = snap.Metric(version=1, Description="btrace metrics")
        new_metric.namespace.add_static_element("intel")
        new_metric.namespace.add_static_element("btrace")
        new_metric.namespace.add_static_element("proc_name")
        new_metric.namespace.add_static_element("metric.namespace[3].value")
        new_metric.data = "stats[proc_name][metric.namespace[3].value]"
        new_metric.timestamp = time.time()
        new_metrics.append(new_metric)
                        



        return new_metrics



    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":

     CollectorBtraceStats().start_plugin()
