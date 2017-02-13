import mock
import os
import time
import unittest

import snap_plugin.v1 as snap
import collector_btrace_metrics as cbm


class Utils:
    def create_mock_metrics(self):
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
                    snap.NamespaceElement(value="emon"),
                    snap.NamespaceElement("cpu","processos number"), # dynamic element
                    snap.NamespaceElement(value=key)
                ],
                version=1,

            )
            metrics.append(metric)
        return metrics


class TestBtraceCollector(unittest.TestCase):
    #@mock.patch('collector_btrace_metrics')
    #@mock.patch('__builtin__.open')
    #@mock.patch('collector_btrace_metrics.CollectThread.__init__')    
        
    @mock.patch('__builtin__.open')
    def test_init_succes(self, mock_open):
        thread = cbm.CollectThread(1, 'Test')
        thread = None

    def test_collect(self):
        utils = Utils()
        metrics = utils.create_mock_metrics()
        result = {'influxd': 
                      {'Reads_Queued': 0, 'Read_Merges': 0, 'Write_Dispatches': 1, 'Write_Dispatches_KiB': 24, 
                       'Write_Merges_KiB': 0, 'Read_Dispatches': 0, 'Timer_unplugs': 0, 'Reads_Completed_KiB': 0, 
                       'Reads_Completed': 0, 'Writes_Requeued': 0, 'Allocation_wait': 4, 'Reads_Queued_KiB': 0, 
                       'Write_Merges': 0, 'Read_Merges_KiB': 0, 'Writes_Queued': 1, 'Reads_Requeued': 0, 
                       'Read_Dispatches_KiB': 0, 'Writes_Queued_KiB': 24, 'IO_unplugs': 1, 'Writes_Completed': 0, 
                       'Writes_Completed_KiB': 0}} 
        collector = cbm.CollectorBtraceStats()
        collector.collect_thread = cbm.CollectThread(1, 'Test')
        collector.collect_thread.collected_metrics_buffer.append(result)
        collector.disable_event = 1
        result = collector.collect(metrics)
        actual =  len(result)
        expected = 22
        self.assertEqual(actual, expected)

    '''
    @mock.patch('__builtin__.open')
    def test_parse_metrics(self, mock_open):
                                   
        mock_result = [ '  8,5   58       84     2.060067718   894  A FWS 0 + 0 <- (252,0) 0',\
                        '  8,0   58       85     2.060068386   894  Q FWS [jbd2/dm-0-8]', \
                        '  8,0   58       86     2.060070488   894  G FWS [jbd2/dm-0-8]', \
                        '  8,0   58       87     2.060071340   894  I FWS (     852) [jbd2/dm-0-8]', \
                        '  8,0   58       88     2.079253365     0  C  WS 0 (2079253365) [0]', \
                        '  8,5   58       89     2.079275216  1863  A WFS 939871056 + 8 <- (252,0) 939869008',\
                        '  8,0   58       90     2.079275640  1863  A WFS 940872528 + 8 <- (8,5) 939871056', \
                        '  8,0   58       91     2.079276602  1863  Q WFS 940872528 + 8 [kworker/58:2]', \
                        'influxd (2414)', \
                        ' Reads Queued:           0,        0KiB\t Writes Queued:           1,       24KiB', \
                        ' Read Dispatches:        0,        0KiB\t Write Dispatches:        1,       24KiB', \
                        ' Reads Requeued:         0\t\t Writes Requeued:         0', \
                        ' Reads Completed:        0,        0KiB\t Writes Completed:        0,        0KiB', \
                        ' Read Merges:            0,        0KiB\t Write Merges:            0,        0KiB', \
                        ' IO unplugs:             1        \t Timer unplugs:           0', \
                        ' Allocation wait:        0        \t Allocation wait:         4', \
                        ' Dispatch wait:          0        \t Dispatch wait:           3', \
                        ' Completion wait:        0        \t Completion wait:       192', \
                        'influxd (112269)', \
                        ' Reads Queued:           0,        0KiB\t Writes Queued:           2,        8KiB',\
                        ' Read Dispatches:        0,        0KiB\t Write Dispatches:        2,        8KiB', \
                        ' Reads Requeued:         0\t\t Writes Requeued:         0', \
                        ' Reads Completed:        0,        0KiB\t Writes Completed:        0,        0KiB', \
                        ' Read Merges:            0,        0KiB\t Write Merges:            0,        0KiB']
        thread = cbm.CollectThread(1, 'Test')
        actual = thread.parse_metrics( mock_result)       
    ''' 
