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
import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

    


class CollectorEmonStats(snap.Collector):
    def __init__(self):
        self.first_time = True
        self.emon_output_file = open("/home/intel/result.txt","r")        
        self.linep = None
        super(self.__class__, self).__init__("collector-emon-metrics-py", 1)
         
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        metric_names =  ['INST_RETIRED.ANY_P','CPU_CLK_UNHALTED.THREAD','MEM_LOAD_UOPS_RETIRED.L3_HIT',
                         'MEM_LOAD_UOPS_RETIRED.L3_MISS','FP_ASSIST.ANY','AVX_INSTS.ALL',
                         'OFFCORE_RESPONSE:request=ALL_REQUESTS:response=LLC_HIT.ANY_RESPONSE',
                         'OFFCORE_RESPONSE:request=ALL_REQUESTS:response=LLC_MISS.ANY_RESPONSE',
                         'UNC_M_CAS_COUNT.RD','UNC_M_CAS_COUNT.WR']
 
                         
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
        LOG.debug(lines)
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
        except Exception as e:
            LOG.debug(e)
            return []
                
        collected_metrics = self.parse_metrics(lines)
        LOG.debug(collected_metrics)
        
        return collected_metrics

        
  
    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
       
        new_metrics = [] 
       
        metrics_dict = self.collect_metrics()
        LOG.debug(metrics_dict)                  
        if metrics_dict == {}:
            LOG.debug("empty metrics")
            return metrics
                

             
        for metric in metrics:             
            LOG.debug(metric)            
            typ = metric.namespace[2].value
           # LOG.debug(metrics_dict[metric.namespace[3].value])
            if typ == '*':
                 try:                        
                     for cpu_num, metric_val in metrics_dict[metric.namespace[3].value].iteritems():
                         LOG.debug(cpu_num, metric_val)   
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
                            
            


        LOG.debug(new_metrics)
        return new_metrics



    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":


     CollectorEmonStats().start_plugin()
