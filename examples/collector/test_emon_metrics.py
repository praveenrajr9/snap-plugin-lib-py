import mock
import unittest

import collector_emon_metrics as cem

class TestEmonCollector(unittest.TestCase):
    @mock.patch('collector_emon_metrics.CollectorThread.follow')
    @mock.patch('__builtin__.open')
    def test_run_none(self, mock_open, mock_follow):
        mock_follow.return_value = None #"INST_RETIRED.ANY_P 1234 10 10 10 10\n =====\n"
        thread = cem.CollectorThread(1, 'Test', 'fake_emon_path')
        actual = thread.run()
        expected = []#["INST_RETIRED.ANY_P 1234 10 10 10 10"]
        self.assertEqual(expected, actual)

    @mock.patch('collector_emon_metrics.CollectorThread.follow')
    @mock.patch('__builtin__.open')
    def test_run_valid(self, mock_open, mock_follow):
        thread = cem.CollectorThread(1, 'Test', 'fake_emon_path')
        mock_follow.return_value = "INST_RETIRED.ANY_P\t1234\t10\t10\t10\t10"
        actual = thread.run()
        expected = None 
        self.assertEqual(expected, actual)
    
    @mock.patch('__builtin__.open')
    def test_init_error(self, mock_open):
        mock_open.side_effect = Exception
        thread = cem.CollectorThread(1, 'Test', 'No_such_file.txt')
        self.assertRaises(Exception)
    
    @mock.patch('__builtin__.open')
    def test_init_succes(self, mock_open):
        thread = cem.CollectorThread(1, 'Test', 'No_such_file.txt')


    @mock.patch('__builtin__.open')
    def test_parse_metrics(self, mock_open):
        thread = cem.CollectorThread(1, 'Test', 'fake_emon_path')
        input_str= ["INST_RETIRED.ANY_P\t1234\t10\t10\t10\t10\n"]
        actual = thread.parse_metrics(input_str)
        expected = {'INST_RETIRED.ANY_P': {'cpu2': '10', 'cpu0': '10', 'cpu1': '10'}}
        self.assertEqual(expected, actual)
        input_str = ["Version 1.0"]
        actual = thread.parse_metrics(input_str)
        expected = {}
        self.assertEqual(expected, actual)
