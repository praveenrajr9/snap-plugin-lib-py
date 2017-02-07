import mock
import unittest

import collector_storage_metrics as csm

class TestStorageCollector(unittest.TestCase):
    
    @mock.patch('__builtin__.open')
    def test_calculate_diff(self):
        storage_io_stats = csm.StorageIOstats()
        
        storage_io_stats.previous_stats =  {{'sda':{{'reads':10},{'writes':10},{'reads_merged':2},
                                                  {'writes_merged':2},{'sectors_read':10},{'sectors_written':10},
						  {'ms_reading':10},{'ms_writing':10},
						  {'weighted_ms_doing_io':10},{'ms_doing_io':10}}},
                                            {'sda1':{{'reads':10},{'writes':10},{'reads_merged':2},
                                                  {'writes_merged':2},{'sectors_read':10},{'sectors_written':10},
                                                  {'ms_reading':10},{'ms_writing':10},
                                                  {'weighted_ms_doing_io':10},{'ms_doing_io':10}}}}
        storage_io_stats.current_stats = {{'sda':{{'reads':15},{'writes':15},{'reads_merged':4},
                                                  {'writes_merged':4},{'sectors_read':10},{'sectors_written':12},
                                                  {'ms_reading':15},{'ms_writing':15},
                                                  {'weighted_ms_doing_io':15},{'ms_doing_io':15}}},
                                           {'sda1':{{'reads':10},{'writes':10},{'reads_merged':4},
                                                  {'writes_merged':4},{'sectors_read':15},{'sectors_written':15},
                                                  {'ms_reading':15},{'ms_writing':15},
                                                  {'weighted_ms_doing_io':15},{'ms_doing_io':15}}}}




        
        expected = storage_io_stats.calculate_diff()
        actual = expected
        print expected
        self.assertEqual(expected, actual)
