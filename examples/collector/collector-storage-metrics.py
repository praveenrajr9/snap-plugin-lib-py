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

class StorageIOstats:

    # http://lxr.osuosl.org/source/Documentation/iostats.txt
    columns_disk = ['major_dev_num', 'minor_dev_num', 'device', 'reads',
                    'reads_merged', 'sectors_read', 'ms_reading', 'writes',
                    'writes_merged', 'sectors_written', 'ms_writing',
                    'current_ios', 'ms_doing_io', 'weighted_ms_doing_io']

    columns_partition = ['major_dev_num', 'minor_dev_num', 'device', 'reads',
                         'sectors_read', 'writes', 'sectors_written']

    file_path = '/proc/diskstats'
    def __init__(self):
        self.previous_stats = []
        self.current_stats = []
        self.devices = []
        self.metric_list = {}

    def read_diskstats(self):

        result = {}
        with open(self.file_path, 'r') as f:
            for line in (l for l in f  if l != ''):
                parts = line.split()
                if len(parts) == len(self.columns_disk):
                    columns = self.columns_disk
                elif len(parts) == len(self.columns_partition):
                    columns = self.columns_partition
                else:
                    continue
                data = dict(zip(self.columns_disk, parts))
                result[data['device']] = dict((k, int(v)) for k, v in data.iteritems() if k != 'device')
                self.devices.append(data['device'])
                #self.metric_list['device'] = data['device']
        return result


    def calculate_diff(self):
        all_reads_per_itv = 0
        all_writes_per_itv = 0
        all_transfer_per_itv = 0
        all_rrqm_per_itv = 0
        all_wrqm_per_itv = 0
        all_rdsec_per_itv = 0
        all_wrsec_per_itv = 0
        all_avgrq_sz = 0.0
        all_avgqu_sz = 0.0
        all_await = 0.0
        all_r_await = 0.0
        all_w_await = 0.0
        all_util = 0.0
        if len(self.current_stats) == len(self.previous_stats):
            for device in self.devices:
                reads_per_itv = self.current_stats[device]['reads'] - self.previous_stats[device]['reads']
                writes_per_itv = self.current_stats[device]['writes'] - self.previous_stats[device]['writes']
                transfer_per_itv = reads_per_itv + writes_per_itv
                rrqm_per_itv = self.current_stats[device]['reads_merged'] - self.previous_stats[device]['reads_merged']
                wrqm_per_itv = self.current_stats[device]['writes_merged'] - self.previous_stats[device]['writes_merged']
                rdsec_per_itv = (self.current_stats[device]['sectors_read'] - self.previous_stats[device]['sectors_read']) * 512
                wrsec_per_itv = (self.current_stats[device]['sectors_written'] - self.previous_stats[device]['sectors_written']) * 512
                avgrq_sz = 0.0
                await_time = 0.0
                r_await = 0.0
                w_await = 0.0
                if transfer_per_itv != 0:
                    avgrq_sz = (rdsec_per_itv + wrsec_per_itv) / transfer_per_itv
                    await_time = (self.current_stats[device]['ms_reading']
                             - self.previous_stats[device]['ms_reading']
                             + (self.current_stats[device]['ms_writing']
                               - self.previous_stats[device]['ms_writing'])) / transfer_per_itv
                avgqu_sz = (self.current_stats[device]['weighted_ms_doing_io'] - self.previous_stats[device]['weighted_ms_doing_io'])/1000.0

                if reads_per_itv != 0:
                    r_await = (self.current_stats[device]['ms_reading']
                               - self.previous_stats[device]['ms_reading']) / reads_per_itv
                if writes_per_itv !=0:
                    w_await = (self.current_stats[device]['ms_writing']
                               - self.previous_stats[device]['ms_writing']) / writes_per_itv
                util = self.current_stats[device]['ms_doing_io'] - self.previous_stats[device]['ms_doing_io']
                util = util / 10.0


                all_reads_per_itv = all_reads_per_itv + reads_per_itv
                all_writes_per_itv = all_writes_per_itv + writes_per_itv
                all_transfer_per_itv = all_transfer_per_itv + transfer_per_itv
                all_rrqm_per_itv = all_rrqm_per_itv + rrqm_per_itv
                all_wrqm_per_itv = all_wrqm_per_itv + wrqm_per_itv
                all_rdsec_per_itv = all_rdsec_per_itv + rdsec_per_itv
                all_wrsec_per_itv = all_wrsec_per_itv + wrsec_per_itv
                all_avgrq_sz = all_avgrq_sz + avgrq_sz
                all_avgqu_sz = all_avgqu_sz + avgqu_sz
                all_await = all_await + await_time
                all_r_await = all_r_await + r_await
                all_w_await = all_w_await + w_await
                all_util = all_util + util


                self.metric_list[device] = {}
                self.metric_list[device]['reads_per_itv'] = reads_per_itv
                self.metric_list[device]['writes_per_itv'] = writes_per_itv
                self.metric_list[device]['transfer_per_itv'] = transfer_per_itv
                self.metric_list[device]['rrqm_per_itv'] = rrqm_per_itv
                self.metric_list[device]['wrqm_per_itv'] = wrqm_per_itv
                self.metric_list[device]['rdsec_per_itv'] = rdsec_per_itv
                self.metric_list[device]['wrsec_per_itv'] = wrsec_per_itv
                self.metric_list[device]['avgrq_sz'] = avgrq_sz
                self.metric_list[device]['await'] = await_time
                self.metric_list[device]['avgqu_sz'] = avgqu_sz
                self.metric_list[device]['r_await'] = r_await
                self.metric_list[device]['w_await'] = w_await
                self.metric_list[device]['util'] = util
        all_util = all_util / len(self.current_stats)
        self.metric_list['ALL'] = {}
        self.metric_list['ALL']['reads_per_itv'] = all_reads_per_itv
        self.metric_list['ALL']['writes_per_itv'] = all_writes_per_itv
        self.metric_list['ALL']['transfer_per_itv'] = all_transfer_per_itv
        self.metric_list['ALL']['rrqm_per_itv'] = all_rrqm_per_itv
        self.metric_list['ALL']['wrqm_per_itv'] = all_wrqm_per_itv
        self.metric_list['ALL']['rdsec_per_itv'] = all_rdsec_per_itv
        self.metric_list['ALL']['wrsec_per_itv'] = all_wrsec_per_itv
        self.metric_list['ALL']['avgrq_sz'] = all_avgrq_sz
        self.metric_list['ALL']['await'] = all_await
        self.metric_list['ALL']['avgqu_sz'] = all_avgqu_sz
        self.metric_list['ALL']['r_await'] = all_r_await
        self.metric_list['ALL']['w_await'] = all_w_await
        self.metric_list['ALL']['util'] = all_util
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
            LOG.debug(self.storage_io_stats.previous_stats, self.storage_io_stats.current_stats)
            for metric in metrics:
               # print metrics
	        dev_type = metric.namespace[3].value
                if dev_type == '*':
                    for device in devices_stat_list:
                        new_metric = snap.Metric(version=1, Description="IO Stats Metrics")
                        new_metric.namespace.add_static_element("intel")
                        new_metric.namespace.add_static_element("storageIOstats")
                        new_metric.namespace.add_static_element("device")
                        new_metric.namespace.add_static_element(device)
                        new_metric.namespace.add_static_element(metric.namespace[4].value)
                        #metric.namespace[3].value = device
                        new_metric.data = devices_stat_list[device][metric.namespace[4].value]
                        new_metric.timestamp = time.time()
                        new_metrics.append(new_metric)
	        else:
                    try:
                        new_metric = snap.Metric(version=1, Description="IO Stats Metrics")
                        new_metric.namespace.add_static_element("intel")
                        new_metric.namespace.add_static_element("storageIOstats")
                        new_metric.namespace.add_static_element("device")
                        new_metric.namespace.add_static_element(dev_type)
                        new_metric.namespace.add_static_element(metric.namespace[4].value)
                        new_metric.data = devices_stat_list[dev_type][metric.namespace[4].value]
                        new_metric.timestamp = time.time()
                        new_metrics.append(new_metric)
                    except Exception as e:
                        LOG.debug(e)



        return new_metrics


    def get_config_policy(self):
        LOG.debug("GetConfigPolicy called")
        return snap.ConfigPolicy()



if __name__ == "__main__":

    StorageIOMetrics().start_plugin()
