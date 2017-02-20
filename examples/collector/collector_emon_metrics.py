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
import ConfigParser as ConfigParser

LOG = logging.getLogger(__name__)
    
class CollectorThread(threading.Thread):

    def __init__(self, threadID, threadName, emon_output_filepath):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.timestamp = time.time()
        self.collected_metric_buffer = []
        try: 
            self.emon_output_file = open(emon_output_filepath, "r")
        except Exception as e:
            LOG.debug("File does not exist or Cannot be opened.")

    def parse_metrics(self, lines):
        stat = {}
        LOG.debug("Parse metrics called")
        for line in lines:
            if "Version" in line or line == " " or line =="\n":
                continue
            temp_list = line.split("\t")
            metric_name = temp_list[0]
            stat[metric_name] = {}
            for i in range(2,len(temp_list) - 1):
                stat[metric_name]['cpu' + str(i-2)] = temp_list[i]
        return stat

    def follow(self, thefile):
        thefile.seek(0,1)
        while True:
            line = thefile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line


    def run(self):
        LOG.debug("run called")
        loglines = self.follow(self.emon_output_file)
        lines = []
        try:
            for line in loglines:
                if "===" in line:
                    self.timestamp = time.time()
                if "===" in line or "---" in line:
                    collected_metrics = self.parse_metrics(lines)
                    self.collected_metric_buffer.append(collected_metrics)
                    lines = []
                    time.sleep(1)
                    continue
                lines.append(line)
        except Exception as e:
            LOG.debug(e)
            
    
        
class CollectorEmonStats(snap.Collector):

    def __init__(self):
        self.first_time = True
        self.emon_output_filepath = "/opt/intel_snap_plugins/result.txt"
        self.collector_thread = None
        super(self.__class__, self).__init__("collector-emon-metrics-py", 1)
         
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        try:
            config_parser = ConfigParser.ConfigParser()
            config_parser.readfp(open('/etc/emon_snap.conf'))
            metric_names = config_parser.get('Metrics','Metrics_List')
            self.emon_output_filepath = config_parser.get('Paths','Emon_Output_Path')
            metric_names =  metric_names.split(",")
            if metric_names == []:
                LOG.debug("no metric names")
        except Exception as e:
            LOG.debug("Error in config file")
            LOG.debug(e)
            return metrics
                         
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

  
    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
        new_metrics = [] 
         
        if self.first_time == True:
            try:
                self.collector_thread = CollectorThread(1, "CollectorThread", self.emon_output_filepath)      
            except Exception as e:
                LOG.debug("collector_thread could not be created, Error in opening file")
                return metrics
            self.collector_thread.start()
            self.first_time = False
            return metrics

        if self.collector_thread.collected_metric_buffer == []:
            return metrics    
 
        metrics_dict = self.collector_thread.collected_metric_buffer.pop(0)
                
        if metrics_dict == {}:
            LOG.debug("empty metrics")
            return metrics
        timestamp = self.collector_thread.timestamp        
        for metric in metrics:             
            typ = metric.namespace[2].value
            if typ == '*':
                 try:                        
                     for cpu_num, metric_val in metrics_dict[metric.namespace[3].value].iteritems():
                         new_metric = snap.Metric(version=1, Description="emon metrics")
                         new_metric.namespace.add_static_element("intel")
                         new_metric.namespace.add_static_element("emon")
                         new_metric.namespace.add_static_element(cpu_num)
                         new_metric.namespace.add_static_element(metric.namespace[3].value)
                         new_metric.data = int(metric_val)
                         new_metric.timestamp = timestamp
                         new_metrics.append(new_metric)
                 except Exception as e:
                     LOG.debug("Metric Key Error") 
                     continue
        return new_metrics

    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()

if __name__ == "__main__":
     CollectorEmonStats().start_plugin()
