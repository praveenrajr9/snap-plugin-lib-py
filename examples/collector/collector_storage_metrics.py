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

import snap_plugin.v1 as snap
LOG = logging.getLogger(__name__)

class StorageIOstats:

    # http://lxr.osuosl.org/source/Documentation/iostats.txt
    columns_disk = ['major_dev_num', 'minor_dev_num', 'device', 'reads',
                    'reads_merged', 'sectors_read', 'ms_reading', 'writes',
                    'writes_merged', 'sectors_written', 'ms_writing',
                    'current_ios', 'ms_doing_io', 'weighted_ms_doing_io']


    file_path = '/proc/diskstats'
    def __init__(self):
        self.previous_stats = []
        self.current_stats = []
        self.devices = []
        self.metric_list = {}

    def read_diskstats(self):

        result = {}
        try:
            file_read = open(self.file_path, 'r')
            read_lines = file_read.readlines()
        except Exception as e:
            LOG.debug("File does not exist or cannot be opened")
        
        for line in read_lines:
            if line == '' or 'ram' in line or 'loop' in line:
                continue 
            parts = line.split()
            if len(parts) == len(self.columns_disk):
                columns = self.columns_disk
            else:
                continue
            data = dict(zip(self.columns_disk, parts))
            result[data['device']] = dict((k, int(v)) for k, v in data.iteritems() if k != 'device')
            self.devices.append(data['device'])
                
        return result

    #@staticmethod
    #def S_VALUE(curr ,prev):
     #   return float(curr - prev)

    def calculate_diff(self):
 
        if len(self.current_stats) == len(self.previous_stats):
            for device in self.devices:
                reads_per_itv =  float(self.current_stats[device]['reads'] - self.previous_stats[device]['reads'])
                writes_per_itv = float(self.current_stats[device]['writes'] - self.previous_stats[device]['writes'])
                transfer_per_itv = reads_per_itv + writes_per_itv
                rrqm_per_itv = float(self.current_stats[device]['reads_merged'] - self.previous_stats[device]['reads_merged'])
                wrqm_per_itv = float(self.current_stats[device]['writes_merged'] - self.previous_stats[device]['writes_merged'])
                rdsec_per_itv = (self.current_stats[device]['sectors_read'] - self.previous_stats[device]['sectors_read']) * 512
                wrsec_per_itv = (self.current_stats[device]['sectors_written'] - self.previous_stats[device]['sectors_written']) * 512
                avgrq_sz = 0.0
                await_time = 0.0
                r_await = 0.0
                w_await = 0.0
                if transfer_per_itv != 0:
                    avgrq_sz = float((rdsec_per_itv + wrsec_per_itv) / transfer_per_itv)
                    await_time = float((self.current_stats[device]['ms_reading']
                             - self.previous_stats[device]['ms_reading']
                             + (self.current_stats[device]['ms_writing']
                               - self.previous_stats[device]['ms_writing'])) / transfer_per_itv)
                avgqu_sz = float((self.current_stats[device]['weighted_ms_doing_io'] - self.previous_stats[device]['weighted_ms_doing_io'])/1000.0)

                if reads_per_itv != 0:
                    r_await = float((self.current_stats[device]['ms_reading']
                               - self.previous_stats[device]['ms_reading']) / reads_per_itv)
                if writes_per_itv !=0:
                    w_await = float((self.current_stats[device]['ms_writing']
                               - self.previous_stats[device]['ms_writing']) / writes_per_itv)
                util = self.current_stats[device]['ms_doing_io'] - self.previous_stats[device]['ms_doing_io']
                util = util / 10.0

                self.metric_list[device] = {}
                storage_stats = {}
                storage_stats['reads_per_itv'] = reads_per_itv
                storage_stats['writes_per_itv'] = writes_per_itv
                storage_stats['transfer_per_itv'] = transfer_per_itv
                storage_stats['rrqm_per_itv'] = rrqm_per_itv
                storage_stats['wrqm_per_itv'] = wrqm_per_itv
                storage_stats['rdsec_per_itv'] = rdsec_per_itv
                storage_stats['wrsec_per_itv'] = wrsec_per_itv
                storage_stats['avgrq_sz'] = avgrq_sz
                storage_stats['await'] = await_time
                storage_stats['avgqu_sz'] = avgqu_sz
                storage_stats['r_await'] = r_await
                storage_stats['w_await'] = w_await
                storage_stats['util'] = util
                self.metric_list[device] = storage_stats
        return self.metric_list


class StorageIOMetrics(snap.Collector):
    def __init__(self):
        self.start_collector = True
        super(self.__class__, self).__init__("collector-storage-metrics-py", 1)
 
         
    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")

  
 
        metrics = []
        metric_names = ['reads_per_itv', 'writes_per_itv', 'transfer_per_itv',
                        'rrqm_per_itv', 'wrqm_per_itv', 'rdsec_per_itv',
                        'wrsec_per_itv', 'avgrq_sz', 'await', 'avgqu_sz',
                        'r_await', 'w_await', 'util']
        for key in metric_names:
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="storageIOstats"),
                    snap.NamespaceElement(value="device"),
                    snap.NamespaceElement(name="device", description="current device name"),
                    snap.NamespaceElement(value=key)
                ],
                version=1,
                
            )
            metrics.append(metric)
        return metrics


    def collect(self, metrics):
        LOG.debug("CollectMetrics called")
        new_metrics = []
        if self.start_collector:
            self.storage_io_stats = StorageIOstats()
            self.storage_io_stats.current_stats = self.storage_io_stats.read_diskstats()
            self.start_collector = False
            return metrics
        else:
            
           
            self.storage_io_stats.previous_stats = self.storage_io_stats.current_stats
            self.storage_io_stats.current_stats = self.storage_io_stats.read_diskstats()
            devices_stat_list = self.storage_io_stats.calculate_diff()
            timestamp = time.time()    
            for metric in metrics:
               
	        dev_type = metric.namespace[3].value
                if dev_type == '*':
                    for device in devices_stat_list:
                        try:
                            new_metric = snap.Metric(version=1, Description="IO Stats Metrics")
                            new_metric.namespace.add_static_element("intel")
                            new_metric.namespace.add_static_element("storageIOstats")
                            new_metric.namespace.add_static_element("device")
                            new_metric.namespace.add_static_element(device)
                            new_metric.namespace.add_static_element(metric.namespace[4].value)                            
                            new_metric.data = devices_stat_list[device][metric.namespace[4].value]
                            new_metric.timestamp = timestamp
                            new_metrics.append(new_metric)
                        except Exception as e:
                            LOG.debug(e)
                            continue
	        else:
                    try:
                        new_metric = snap.Metric(version=1, Description="IO Stats Metrics")
                        new_metric.namespace.add_static_element("intel")
                        new_metric.namespace.add_static_element("storageIOstats")
                        new_metric.namespace.add_static_element("device")
                        new_metric.namespace.add_static_element(dev_type)
                        new_metric.namespace.add_static_element(metric.namespace[4].value)
                        new_metric.data = devices_stat_list[dev_type][metric.namespace[4].value]
                        new_metric.timestamp = timestamp
                        new_metrics.append(new_metric)
                    except Exception as e:
                        LOG.debug(e)
                        continue



        return new_metrics


    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":

    StorageIOMetrics().start_plugin()
