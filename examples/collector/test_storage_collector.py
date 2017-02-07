import mock
import unittest

import collector_storage_metrics as csm

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
