import unittest
import sys

#sys.path.append('..')
from reporting.parsers import JsonGrepParser


class JsonGrepParserTestCase(unittest.TestCase):
    def test_case1(self):
        parser=JsonGrepParser(pattern="chargebackData", list_name="hcp-chargeback")
        input= '{"chargebackData":[{"systemName":"hcp1.s3.ersa.edu.au"}, {"systemName":"hcp2.s3.ersa.edu.au"}]}'
        output=parser.parse(input)
        #print output
        self.assertTrue('timestamp' in output)
        self.assertTrue('hostname' in output)
        self.assertTrue('hcp-chargeback' in output)
        self.assertDictEqual({"hcp-chargeback": output["hcp-chargeback"]}, {"hcp-chargeback": [{u'systemName':u'hcp1.s3.ersa.edu.au'}, {u'systemName':u'hcp2.s3.ersa.edu.au'}]})

    def test_case2(self):
        parser=JsonGrepParser(pattern="chargebackData", list_name="hcp-chargeback")
        input= '{"chargebackData":["chargebackData1","chargebackData2"]}'
        output=parser.parse(input)
        #print output
        self.assertTrue('timestamp' in output)
        self.assertTrue('hostname' in output)
        self.assertTrue('hcp-chargeback' in output)
        self.assertDictEqual({"hcp-chargeback": output["hcp-chargeback"]}, {"hcp-chargeback": [u'chargebackData1',u'chargebackData2']})

    def test_case3(self):
        parser=JsonGrepParser(pattern=". chargebackData", list_name="hcp-chargeback")
        input= '[{"chargebackData": 1}, {"chargebackData": 2}]'
        output=parser.parse(input)
        #print output
        self.assertTrue('timestamp' in output)
        self.assertTrue('hostname' in output)
        self.assertTrue('hcp-chargeback' in output)
        self.assertDictEqual({"hcp-chargeback": output["hcp-chargeback"]}, {"hcp-chargeback": [1, 2]})
        
if __name__ == '__main__':
    unittest.main()
