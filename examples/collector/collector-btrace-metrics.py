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
import threading
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

collected_metrics_buffer = []

class CollectThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.per_proc_stats_list = []
        self.throughput_stats = {}

    
    def run(self):
        while True:
            LOG.debug("run started run")
            metric_collected = self.collect_metrics()
            LOG.debug(metric_collected)
            collected_metrics_buffer.append(metric_collected)

    def collect_metrics(self):
        LOG.debug("collect_metrics called")
        try:
            self.proc = sub.Popen(["btrace","-s","-t","-w","5","/dev/sda"],stdout=sub.PIPE)
            self.result = self.proc.communicate()
        except Exception as e:
            LOG.debug("collect_metrics")
            LOG.debug(e)
            return []
        #try:
         #   self.proc = sub.Popen(["btrace","-s","-t","-w","5","/dev/sda"],stdout=sub.PIPE)
        #except Exception as e:
         #   LOG.debug(e)
            #return []


        if len(self.result[0]) == 1:
            LOG.debug("No metrics")
            return []
        try:
            self.result = self.result[0].split("\n")
            collected_metrics = self.parse_metrics(self.result)
        except Exception as e:
            return []
        LOG.debug("collected_metrics")
        LOG.debug(collected_metrics)
        return collected_metrics


    def parse_metrics(self, result):
        i=0
        LOG.debug(result)
        self.per_proc_stats_list = []
        while i < range(len(result)-1):
            try:
                temp_list = result[i].split()
                len_temp_list = len(temp_list)
                if len_temp_list == 2 and len_temp_list != 0:
                    self.fill_per_proc_data(result, i, temp_list[0])
                    i = i + 8
                    continue
                if len_temp_list == 5 and len_temp_list != 0:
                    self.throughput_stats = self.fill_throughput_data(result, i)
                    break
                i = i + 1
            except Exception as e:
               LOG.debug(e)

        #LOG.debug(self.per_proc_stats_list)
        return self.per_proc_stats_list



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
                    temp_key = temp_key.replace(" ","_")
                    temp_val = val[1].split(",")


                    stats[temp_key] = int(temp_val[0].strip())
                    if (len(temp_val) == 2):
                        temp_val[1] = re.split("(\d+)",temp_val[1])[1]

                        stats[temp_key +"_KiB"] = int(temp_val[1].strip())


        except Exception as e:
            LOG.debug(e)
        per_proc_stats[proc_num] = stats
        self.per_proc_stats_list.append(per_proc_stats)


    def fill_throughput_data(self, result, i):
        stats = {}
        throughput = result[i].split(":")
        read_writes = throughput[1].split(" / ")
        stats[throughput[0]] = read_writes

        events = result[i+1].split(":")
        stats[events[0]] = events[1]


        return stats


class IOBtraceStats:
    def __init__(self):
        self.per_proc_stats_list = []
        self.throughput_stats = {}
        


class CollectorBtraceStats(snap.Collector):
    def __init__(self):
        self.disable_event = 0
        # collect_thread = CollectThread(1, "Thread-1", 1)
        # collect_thread.start()
        super(self.__class__, self).__init__("collector-btrace-metrics-py", 1)
         
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names =  ['Reads_Queued','Reads_Queued_KiB', 'Read_Dispatches',
                        'Read_Dispatches_KiB', 'Reads_Requeued', 'Reads_Completed', 
                        'Reads_Completed_KiB', 'Read_Merges', 'Read_Merges_KiB',
                        'Read_depth', 'Writes_Queued', 'Writes_Queued_KiB', 
                        'Write_Dispatches', 'Write_Dispatches_KiB', 'Writes_Requeued',
                        'Writes_Completed','Writes_Completed_KiB', 'Write_Merges', 
                        'Write_Merges_KiB', 'Write_depth', 'IO_unplugs', 'Timer_unplugs' 
                         ]
 
                         
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
    
    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
       
        new_metrics = [] 
        if self.disable_event == 0:
            self.disable_event = 1
            #self.proc = sub.Popen(["btrace","-s","-t","-w","5","/dev/sda"],stdout=sub.PIPE)
            LOG.debug("first time ")
            collect_thread = CollectThread(1, "Thread-1", 1)
            collect_thread.start()
            return metrics
        if collected_metrics_buffer == []:
            return metrics
        metric_list = collected_metrics_buffer.pop(0)
        
                    
        if len(metric_list) <= 1:
            LOG.debug("empty metrics")
            return metrics
                

        for stats in metric_list:
            proc_name = stats.keys()[0]
            
            for metric in metrics:
                typ = metric.namespace[2].value
                if typ == '*':
                    try:                        
                        LOG.debug(stats[proc_name][metric.namespace[3].value])
                        LOG.debug(metric.namespace[3].value)
                        LOG.debug(stats[proc_name]) 
                        new_metric = snap.Metric(version=1, Description="btrace metrics")
                        new_metric.namespace.add_static_element("intel")
                        new_metric.namespace.add_static_element("btrace")
                        new_metric.namespace.add_static_element(proc_name)
                        new_metric.namespace.add_static_element(metric.namespace[3].value)
                        new_metric.data = stats[proc_name][metric.namespace[3].value]
                        new_metric.timestamp = time.time()
                        new_metrics.append(new_metric)
                    except Exception as e:
                        LOG.debug("metric key error") 
                        LOG.debug(e)
                        continue

        return new_metrics



    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":

    CollectorBtraceStats().start_plugin()
