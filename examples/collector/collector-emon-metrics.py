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
import threading
import re
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)


#class Stats:
#     def __init__(self):
#        self.collected_metric_buffer = []    
collected_metric_buffer = []   

    
class CollectorThread(threading.Thread):

    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.emon_output_file = open("/tmp/asnaraya/result.txt","r")
        self.linep = None
        #self.stats = Stats()

    def parse_metrics(self, lines):
        stat = {}
        LOG.debug("parse_metrics called")
        #LOG.debug(lines)
        for line in lines:
            if "Version" in line or line == " " or line =="\n":
                continue
            temp_list = line.split("\t")
            metric_name = temp_list[0]
            stat[metric_name] = {}
            for i in range(2,len(temp_list)-1):
                stat[metric_name]['cpu'+str(i-1)] = temp_list[i]
        return stat



    def collect_metrics(self):
        LOG.debug("collect_metrics called")
        line = self.linep
        lines = []
        try:
            for line in self.emon_output_file:
                if "===" in line:
                    self.linep = line
                    break
                lines.append(line)
         #       LOG.debug(line)
        except Exception as e:
            LOG.debug(e)
            return []

        collected_metrics = self.parse_metrics(lines)
        #LOG.debug(collected_metrics)
        return collected_metrics




    def follow(self, thefile):
        thefile.seek(0,1)
        while True:
            line = thefile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line


    def run(self):
       # while True:
           # metrics = self.collect_metrics()        
           # self.stats.collected_metric_buffer.append(metrics)
            #collected_metric_buffer.append(metrics)
        #    LOG.debug(collected_metric_buffer)
           # LOG.debug(len(collected_metric_buffer))
           # time.sleep(1) 
        LOG.debug("run called")
        line = self.linep
        loglines = self.follow(self.emon_output_file)
        lines = []
        try:
            for line in loglines:
                if "===" in line or "---" in line:
                    #self.linep = line
                    
                    collected_metrics = self.parse_metrics(lines)
                    collected_metric_buffer.append(collected_metrics)
                    LOG.debug(lines)
                    lines = []
                    time.sleep(1)
                    
                    continue
                
                lines.append(line)
         #       LOG.debug(line)
        except Exception as e:
            LOG.debug(e)
            return []
        LOG.debug("came out of file run stopped")
       # collected_metrics = self.parse_metrics(lines)
        #LOG.debug(collected_metrics)
        #return collected_metrics
    
        
class CollectorEmonStats(snap.Collector):

    def __init__(self):
        self.first_time = True
        #self.emon_output_file = open("/home/intel/result.txt","r")        
        self.linep = None
        super(self.__class__, self).__init__("collector-emon-metrics-py", 1)
         
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names = ['INST_RETIRED.ANY_P','CPU_CLK_UNHALTED.THREAD','MEM_UOPS_RETIRED.L2_HIT_LOADS','MEM_UOPS_RETIRED.L2_MISS_LOADS',
                        'UOPS_RETIRED.PACKED_SIMD','UOPS_RETIRED.SCALAR_SIMD','CYCLES_DIV_BUSY.ALL','MACHINE_CLEARS.FP_ASSIST',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=ANY_RESPONSE','OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_FAR','OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_FAR']
 
                         
        for key in metric_names:
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="emon"),
                    snap.NamespaceElement("cpu","processos number"), # dynamic element
                    snap.NamespaceElement(value=key)
                ],
                version=1,
                
            )
            metrics.append(metric)
        return metrics

    def parse_metrics(self, lines):
        stat = {}
        LOG.debug("parse_metrics called")
        #LOG.debug(lines)
        for line in lines:
            if "Version" in line or line == " " or line =="\n":
                continue
            temp_list = line.split("\t")
            metric_name = temp_list[0]
            stat[metric_name] = {}
            for i in range(2,len(temp_list)-1):
                stat[metric_name]['cpu'+str(i-1)] = temp_list[i]
        return stat

    def collect_metrics(self):
        LOG.debug("collect_metrics called")
        line = self.linep
        lines = []
        try:
            for line in self.emon_output_file:
                if "===" in line:
                    self.linep = line
                    break
                lines.append(line)
                #LOG.debug(line)
        except Exception as e:
            #LOG.debug(e)
            return []
                
        collected_metrics = self.parse_metrics(lines)
        #LOG.debug(collected_metrics)
        
        return collected_metrics

        
  
    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
       
        new_metrics = [] 
	if self.first_time == True:
           collector_thread = CollectorThread(1, "CollectorThread", 1)      
           collector_thread.start()
           self.first_time = False
           return metrics

        if collected_metric_buffer == []:
            return metrics     
        metrics_dict = collected_metric_buffer.pop(0)
                
        LOG.debug(metrics_dict)                  
        if metrics_dict == {}:
            LOG.debug("empty metrics")
            return metrics
                

             
        for metric in metrics:             
            #LOG.debug(metric)            
            typ = metric.namespace[2].value
           # LOG.debug(metrics_dict[metric.namespace[3].value])
            if typ == '*':
                 try:                        
                     for cpu_num, metric_val in metrics_dict[metric.namespace[3].value].iteritems():
             #            LOG.debug(cpu_num, metric_val)   
                         new_metric = snap.Metric(version=1, Description="emon metrics")
                         new_metric.namespace.add_static_element("intel")
                         new_metric.namespace.add_static_element("emon")
                         new_metric.namespace.add_static_element(cpu_num)
                         new_metric.namespace.add_static_element(metric.namespace[3].value)
                         new_metric.data = int(metric_val)
                         new_metric.timestamp = time.time()
                         new_metrics.append(new_metric)
                 except Exception as e:
                     LOG.debug("metric key error") 
                    # LOG.debug(e)
                     continue
                            
            


      #  LOG.debug(new_metrics)
        return new_metrics



    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":


     CollectorEmonStats().start_plugin()
