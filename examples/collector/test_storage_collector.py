import mock
import unittest
import os

import snap_plugin.v1 as snap
import collector_storage_metrics as csm



class SupportClass:

    def __init__(self):
        self.mock_filepath = "/tmp/snap_mock_storage"   
        self.new_mock_filepath = "/tmp/snap_new_mock_storage"

    def create_mock_file(self):
        tmp_file = open(self.mock_filepath, "w")
        tmp_file.write("8       0 sda 489471 2924 40305996 1746480 2078488 752068 636320826 266445728 0 9836360 268192112\n")
        tmp_file.write("8       1 sda1 779 23 17386 8184 438 621 308570 88596 0 8252 96780\n")
        tmp_file.write("8       2 sda2 26 0 32 184 0 0 0 0 0 184 184\n")
        tmp_file.close()

    def remove_mock_file(self):
        try:
            os.remove(self.mock_filepath)
        except Exception as e:
            print e

    def create_new_mock_file(self):
        tmp_file = open(self.new_mock_filepath, "w")
        tmp_file.write("8       0 sda 489505 2924 40306756 1746988 2084051 754086 636523898 266472148 0 9859620 268219036\n")
        tmp_file.write("8       1 sda1 779 23 17386 8184 438 621 308570 88596 0 8252 96780\n")
        tmp_file.write("8       2 sda2 26 0 32 184 0 0 0 0 0 184 184\n")
        tmp_file.close()

    def create_mock_metrics(self):                
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

        

class TestStorageCollector(unittest.TestCase):
    
    @mock.patch('__builtin__.open')
    def test_calculate_diff(self, mockopen):
        storage_io_stats = csm.StorageIOstats()
        storage_io_stats.devices = ['sda','sda1']        
        storage_io_stats.previous_stats =  {'sda':{'reads':10, 'writes':10, 'reads_merged':2, 'writes_merged':2,
                                                  'sectors_read':10, 'sectors_written':10, 'ms_reading':10,
						   'ms_writing':10, 'weighted_ms_doing_io':10, 'ms_doing_io':10},
                                            'sda1':{'reads':10, 'writes':10, 'reads_merged':2, 'writes_merged':2,
                                                    'sectors_read':10, 'sectors_written':10, 'ms_reading':10,
                                                    'ms_writing':10, 'weighted_ms_doing_io':10, 'ms_doing_io':10}}
        storage_io_stats.current_stats = {'sda':{'reads':15, 'writes':15, 'reads_merged':4, 'writes_merged':4,
                                                 'sectors_read':10, 'sectors_written':12, 'ms_reading':15,
                                                 'ms_writing':15, 'weighted_ms_doing_io':15, 'ms_doing_io':15},
                                           'sda1':{'reads':10, 'writes':10, 'reads_merged':4,
                                                  'writes_merged':4, 'sectors_read':15, 'sectors_written':15,
                                                  'ms_reading':15, 'ms_writing':15,
                                                  'weighted_ms_doing_io':15, 'ms_doing_io':15}}




        
        expected = storage_io_stats.calculate_diff()
        actual = {'ALL':{'reads_per_itv': 5.0, 'writes_per_itv': 5.0, 'avgqu_sz': 0.01, 'rdsec_per_itv': 2560.0, 
                         'util': 0.5, 'await': 1.0, 'wrsec_per_itv': 3584.0, 'avgrq_sz': 102.4, 
                         'rrqm_per_itv': 4.0, 'r_await': 1.0, 'transfer_per_itv': 10.0, 'wrqm_per_itv': 4.0, 'w_await': 1.0}, 
                  'sda': {'reads_per_itv': 5.0, 'writes_per_itv': 5.0, 'avgqu_sz': 0.005, 'rdsec_per_itv': 0, 
                          'util': 0.5, 'await': 1.0, 'wrsec_per_itv': 1024, 'avgrq_sz': 102.4, 'rrqm_per_itv': 2.0, 
                          'r_await': 1.0, 'transfer_per_itv': 10.0, 'wrqm_per_itv': 2.0, 'w_await': 1.0}, 
                  'sda1': {'reads_per_itv': 0.0, 'writes_per_itv': 0.0, 'avgqu_sz': 0.005, 'rdsec_per_itv': 2560, 
                           'util': 0.5, 'await': 0.0, 'wrsec_per_itv': 2560, 'avgrq_sz': 0.0, 'rrqm_per_itv': 2.0, 
                           'r_await': 0.0, 'transfer_per_itv': 0.0, 'wrqm_per_itv': 2.0, 'w_await': 0.0}}
        
        self.assertEqual(expected, actual)

    def test_read_diskstats_success(self):
        storage_io_stats = csm.StorageIOstats()
        support_class = SupportClass()
        support_class.create_mock_file()
        storage_io_stats.file_path = support_class.mock_filepath
        actual = storage_io_stats.read_diskstats()
        expected = {'sda2': {'ms_writing': 0, 'sectors_read': 32, 'reads_merged': 0, 'ms_doing_io': 184, 
                             'writes': 0, 'minor_dev_num': 2, 'reads': 26, 'sectors_written': 0, 
                             'writes_merged': 0, 'current_ios': 0, 'ms_reading': 184, 'major_dev_num': 8, 
                             'weighted_ms_doing_io': 184}, 
                    'sda': {'ms_writing': 266445728, 'sectors_read': 40305996, 'reads_merged': 2924, 
                            'ms_doing_io': 9836360, 'writes': 2078488, 'minor_dev_num': 0, 'reads': 489471, 
                            'sectors_written': 636320826, 'writes_merged': 752068, 'current_ios': 0, 'ms_reading': 1746480, 
                            'major_dev_num': 8, 'weighted_ms_doing_io': 268192112}, 
                    'sda1': {'ms_writing': 88596, 'sectors_read': 17386, 'reads_merged': 23, 'ms_doing_io': 8252, 
                             'writes': 438, 'minor_dev_num': 1, 'reads': 779, 'sectors_written': 308570, 'writes_merged': 621, 
                             'current_ios': 0, 'ms_reading': 8184, 'major_dev_num': 8, 'weighted_ms_doing_io': 96780}}
        self.assertEqual(actual, expected) 
        support_class.remove_mock_file()

    def test_read_diskstats_fail(self):
        storage_io_stats = csm.StorageIOstats()
        support_class = SupportClass()
        support_class.create_mock_file()
        storage_io_stats.file_path = support_class.mock_filepath
        actual = storage_io_stats.read_diskstats()
        expected = {'sda2': {'ms_writing': 0, 'sectors_read': 100, 'reads_merged': 0, 'ms_doing_io': 184,
                             'writes': 0, 'reads': 26, 'sectors_written': 0,
                             'writes_merged': 0, 'current_ios': 0, 'ms_reading': 184, 'major_dev_num': 8,
                             'weighted_ms_doing_io': 184},
                    'sda': {'ms_writing': 266445728, 'sectors_read': 40305996, 'reads_merged': 2924,
                            'ms_doing_io': 9836360, 'writes': 2078488, 'minor_dev_num': 0, 'reads': 489471,
                            'sectors_written': 636320826, 'writes_merged': 752068, 'current_ios': 0, 'ms_reading': 1746480,
                            'major_dev_num': 8, 'weighted_ms_doing_io': 268192112},
                    'sda1': {'ms_writing': 88596, 'sectors_read': 17386, 'reads_merged': 23, 'ms_doing_io': 8252,
                             'writes': 438, 'minor_dev_num': 1, 'reads': 779, 'sectors_written': 308570, 'writes_merged': 621,
                             'current_ios': 0, 'ms_reading': 8184, 'major_dev_num': 8, 'weighted_ms_doing_io': 96780}}
        self.assertNotEqual(actual, expected)
        
        support_class.remove_mock_file()




    def test_collect(self):
        support_class = SupportClass()
        support_class.create_new_mock_file()
        storage_io_stats = csm.StorageIOstats()
        storage_io_stats.current_stats = {'sda2': {'ms_writing': 0, 'sectors_read': 32, 'reads_merged': 0, 'ms_doing_io': 184,
                                                   'writes': 0, 'minor_dev_num': 2, 'reads': 26, 'sectors_written': 0,
                                                   'writes_merged': 0, 'current_ios': 0, 'ms_reading': 184, 'major_dev_num': 8,
                                                   'weighted_ms_doing_io': 184},
                                           'sda': {'ms_writing': 266445728, 'sectors_read': 40305996, 'reads_merged': 2924,
                                                   'ms_doing_io': 9836360, 'writes': 2078488, 'minor_dev_num': 0, 'reads': 489471,
                                                   'sectors_written': 636320826, 'writes_merged': 752068, 'current_ios': 0, 'ms_reading': 1746480,
                                                   'major_dev_num': 8, 'weighted_ms_doing_io': 268192112},
                                           'sda1': {'ms_writing': 88596, 'sectors_read': 17386, 'reads_merged': 23, 'ms_doing_io': 8252,
                                                    'writes': 438, 'minor_dev_num': 1, 'reads': 779, 'sectors_written': 308570, 'writes_merged': 621,
                                                    'current_ios': 0, 'ms_reading': 8184, 'major_dev_num': 8, 'weighted_ms_doing_io': 96780}}
       
        storage_io_stats.devices = ['sda','sda1','sda2']
        
        storage_io_stats.file_path = support_class.new_mock_filepath
        storage_io_metrics = csm.StorageIOMetrics()
        storage_io_metrics.start_collector = False
        storage_io_metrics.storage_io_stats = storage_io_stats
        metrics = support_class.create_mock_metrics()
        actual = len(storage_io_metrics.collect(metrics))
        expected = 52
        self.assertEqual(actual, expected)

    def test_collect_first_time_success(self):
        support_class = SupportClass()
        metrics = support_class.create_mock_metrics()
        storage_io_metrics = csm.StorageIOMetrics()
        storage_io_metrics.start_collector = True
        actual = storage_io_metrics.collect(metrics)
        print actual
        expected = metrics
        self.assertEqual(actual, expected)
        
       
