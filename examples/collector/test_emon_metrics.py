import mock
import unittest

import collector_emon_metrics as cem

class TestEmonCollector(unittest.TestCase):
    @mock.patch('collector_emon_metrics.CollectorThread.follow')
    @mock.patch('__builtin__.open')
    def test_run(self, mock_open, mock_follow):
        mock_follow.returnvalue = "INST_RETIRED.ANY_P 1234 10 10 10 10\n ====="
        thread = cem.CollectorThread(1, 'Test', 'fake_emon_path')
        actual = thread.run()
        expected = ["INST_RETIRED.ANY_P 1234 10 10 10 10"]
        self.assertEqual(expected, actual)


    @mock.patch('__builtin__.open')
    def test_init(self, mock_open):
        mock_open.side_effect = Exception
        thread = cem.CollectorThread('')
        self.assertRaises(Exception)
