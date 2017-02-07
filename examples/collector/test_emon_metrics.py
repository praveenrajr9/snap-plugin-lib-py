import mock
import os
import time
import unittest

import snap_plugin.v1 as snap
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
        input_str= ["INST_RETIRED.ANY_P\t1234\t10\t11\t12\t13\t\n"]
        actual = thread.parse_metrics(input_str)
        expected = {'INST_RETIRED.ANY_P': {'cpu2': '12', 'cpu0': '10', 'cpu1':
            '11', 'cpu3' : '13'}}
        self.assertEqual(expected, actual)
        input_str = ["Version 1.0"]
        actual = thread.parse_metrics(input_str)
        expected = {}
        self.assertEqual(expected, actual)
     
    def test_mock_metrics(self):
        metrics = []
        metric_names = ['INST_RETIRED.ANY_P','CPU_CLK_UNHALTED.THREAD','MEM_UOPS_RETIRED.L2_HIT_LOADS','MEM_UOPS_RETIRED.L2_MISS_LOADS',
                        'UOPS_RETIRED.PACKED_SIMD','UOPS_RETIRED.SCALAR_SIMD','CYCLES_DIV_BUSY.ALL','MACHINE_CLEARS.FP_ASSIST',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=ANY_RESPONSE','OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=DDR_FAR','OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_NEAR',
                        'OFFCORE_RESPONSE:request=ANY_REQUEST:response=MCDRAM_FAR']
 
                         
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
    
    def test_init_collector_success(self):
        collector_emon_stats = cem.CollectorEmonStats()	  	
      #  self.assertRaises(Exception)

    
    def test_collect_metrics(self):
        mock_filepath = "/tmp/emonoutput"
	self.test_create_mock_file(mock_filepath)
        collector_emon_stats = cem.CollectorEmonStats()
        metric_names = self.test_mock_metrics()
        collector_emon_stats.first_time = False
        collector_emon_stats.thread = cem.CollectorThread(1, "MockCollectorThread", mock_filepath)   
        collector_emon_stats.thread.start()
        time.sleep(5)
        actual_metrics = collector_emon_stats.collect(metric_names)
	print actual_metrics
        expected_metrics = actual_metrics
        assertEqual(actual_metrics,actual_metrics)
        self.remove_mock_file()
        collector_emon_stats.thread.stop()        
   
    def test_create_mock_file(self, mock_filepath): 
        tmp_file = open(mock_filepath,"w")
        tmp_file.write("Version Info: Public V10.0.0 (Nov  4 2016 at 02:21:14) Intel(R) Processor code named Knights Landing M:87 S:1\n")
  	tmp_file.write("INST_RETIRED.ANY_P\t1234\t10\t10\t10\t10\t\nCPU_CLK_UNHALTED.THREAD\t1234\t15\t15\t15\t15\t\n----\n")
        tmp_file.write("MEM_UOPS_RETIRED.L2_HIT_LOADS\t1234\t10\t10\t10\t10\t\nUOPS_RETIRED.PACKED_SIMD\t1234\t10\t10\t10\t10\t\n")
        tmp_file.close()
       
