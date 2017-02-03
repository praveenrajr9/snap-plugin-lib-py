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

# collector buffer
collected_metric_buffer = []   

class SharedObjects:
    def __init__(self):
	self.topology_tree = None
	self.pd_table = None
    
class CollectorThread(threading.Thread):

    def __init__(self, threadID, name, counter, shared_objs):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.emon_output_file = open("/home/intel/result.txt","r")
        self.shared_objs = shared_objs
      

    def add_to_tree(self, metric_name, core_num, val):
      
        LOG.debug("add to topology_tree")
        pd_table = self.shared_objs.pd_table
        topology_tree = self.shared_objs.topology_tree
        try:
            physical_proc = pd_table[core_num][0]
            logical_proc = pd_table[core_num][1]
            tile = pd_table[core_num][2]
            topology_tree[physical_proc][logical_proc][tile][core_num][metric_name] = val
        except Exception as e:
             LOG.debug(e)
             LOG.debug("add_to_tree_error")
        self.shared_objs.topology_tree = topology_tree

    def aggregate_metrics(self, stat):
        topology_tree = self.shared_objs.topology_tree     
        for name, value in stat.iteritems():
            for physical_proc in topology_tree:
                p_proc_sum = 0
                for logicalp in topology_tree[physical_proc]:
                    l_proc_sum = 0
                    for tile in topology_tree[physical_proc][logicalp]:
                        t_num_sum = 0
                        for os_core in topology_tree[physical_proc][logicalp][tile]:
                            try: 
                                core_value = topology_tree[physical_proc][logicalp][tile][os_core][name]
                                if topology_tree[physical_proc][logicalp][tile][os_core] == {}:
                                   continue
                                t_num_sum = t_num_sum + int(core_value)
                            except Exception as e:
                                LOG.debug(e)
                                continue
                        stat[name]["p" + str(physical_proc) + "-l" + str(logicalp) + "-t" + str(tile)] = t_num_sum
                        l_proc_sum = l_proc_sum + t_num_sum
                    stat[name]["p" + str(physical_proc) + "-l" + str(logicalp)] = l_proc_sum
                    p_proc_sum = p_proc_sum +  l_proc_sum
                stat[name]["p"+ str(physical_proc)] =  p_proc_sum
        return stat       

    def parse_metrics(self, lines):
        stat = {}
        LOG.debug("Parse metrics called")
       
        for line in lines:
            if "Version" in line or line == " " or line =="\n":
                continue
            temp_list = line.split("\t")
            metric_name = temp_list[0]
            stat[metric_name] = {}
            for i in range(2,len(temp_list)-1):
                stat[metric_name]['cpu'+str(i-2)] = temp_list[i]
                self.add_to_tree(metric_name, int(i-2), temp_list[i])
        
        stat = self.aggregate_metrics(stat)
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
                if "===" in line or "---" in line:
                    
                    collected_metrics = self.parse_metrics(lines)
                    collected_metric_buffer.append(collected_metrics)
                    lines = []
                    time.sleep(1)
                    
                    continue
                
                lines.append(line)
        except Exception as e:
            LOG.debug(e)
            return []
    
        
class CollectorEmonStats(snap.Collector):

    def __init__(self):
        self.first_time = True
        self.toplogy_tree = None
        self.pd_table = None
        super(self.__class__, self).__init__("collector-emon-aggMetrics-py", 1)
         
    def build_tree(self):
        #global pd_table
        pd_table = []#pd.read_csv('knl_topo.txt', sep="\s+", header = None)
	proc_map_file = open("knl_topo.txt","r")
	lines = proc_map_file.readlines()
        
	proc_tree = {}
	for line in lines:
    
            if line == "\n" or "Processor" in line or "---" in line:
               continue        
	    line_list = line.split()
	    os_core = int(line_list[0])
	    phys_proc = int(line_list[1])
	    logical_proc = int(line_list[3])
            pd_table.append(os_core) 
            pd_table[os_core]=[0,1,2]
            pd_table[os_core][0] = phys_proc
            pd_table[os_core][1] = logical_proc
 
            if len(line_list) >= 5:
                tile = int(line_list[4])
                pd_table[os_core][2] = tile

            
	   
	    if phys_proc not in proc_tree:
	        proc_tree[phys_proc] = {}
	        proc_tree[phys_proc][logical_proc] = {}
	        proc_tree[phys_proc][logical_proc][tile] = {}
	        proc_tree[phys_proc][logical_proc][tile][os_core] = {}

	        continue
	    if logical_proc not in proc_tree[phys_proc]:
	        proc_tree[phys_proc][logical_proc] = {}
	        proc_tree[phys_proc][logical_proc][tile] = {}
	        proc_tree[phys_proc][logical_proc][tile][os_core] = {}
	        continue
	    if tile not in proc_tree[phys_proc][logical_proc]:
	        proc_tree[phys_proc][logical_proc][tile] = {}
	        proc_tree[phys_proc][logical_proc][tile][os_core] = {}

	    if os_core not in proc_tree[phys_proc][logical_proc][tile]:
        	proc_tree[phys_proc][logical_proc][tile][os_core] = {}
        self.pd_table = pd_table 
	return proc_tree
        
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        #try:
        #    config = ConfigParser.ConfigParser()
        #    config.readfp(open('config.txt')
        #    metric_names = config.get('Metrics','Metrics_List')
        #    if metric_names == ''
        #        LOG.debug(no metric names)
        #except Exception as e:
        #    LOG.debug("Error in config file")
        #    LOG.debug(e)
        #    assert(False)
        
        metric_names = ['INST_RETIRED.ANY_P','CPU_CLK_UNHALTED.THREAD','MEM_UOPS_RETIRED.L2_HIT_LOADS','MEM_UOPS_RETIRED.L2_MISS_LOADS',
                        'UOPS_RETIRED.PACKED_SIMD','UOPS_RETIRED.SCALAR_SIMD','CYCLES_DIV_BUSY.ALL','MACHINE_CLEARS.FP_ASSIST',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=ANY_RESPONSE','OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_FAR','OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_FAR']
              
       
        #LOG.debug(topology_tree)                 
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

           shared_objs = SharedObjects()         
           shared_objs.topology_tree = self.build_tree()
           shared_objs.pd_table = self.pd_table
           collector_thread = CollectorThread(1, "CollectorThread", 1, shared_objs)      
           collector_thread.start()
           self.first_time = False
           return metrics

        if collected_metric_buffer == []:
            return metrics    

        metrics_dict = collected_metric_buffer.pop(0)

        if metrics_dict == {}:
            LOG.debug("empty metrics")
            return metrics
        LOG.debug(metrics_dict)        
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
                         new_metric.timestamp = time.time()
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
