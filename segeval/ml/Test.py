'''
Tests the machine learning (ML) statistics functions, and ml package.

.. moduleauthor:: Chris Fournier <chris.m.fournier@gmail.com>
'''
import unittest
from decimal import Decimal
from . import precision, recall, fmeasure, vars_to_cf, cf_to_vars


class TestML(unittest.TestCase):
    '''
    Machine-learning metric tests.
    '''
    #pylint: disable=R0904,C0103
    
    def test_precision(self):
        '''
        Test precision.
        '''
        cf = {}
        cf['tp'] = 1
        cf['fp'] = 1
        self.assertEqual(precision(cf), Decimal('0.5'))
        cf['tp'] = 1
        cf['fp'] = 3
        self.assertEqual(precision(cf), Decimal('0.25'))
        cf['tp'] = 6
        cf['fp'] = 2
        self.assertEqual(precision(cf), Decimal('0.75'))
        cf['tp'] = 0
        cf['fp'] = 2
        self.assertEqual(precision(cf), Decimal('0'))
        cf['tp'] = 2
        cf['fp'] = 0
        self.assertEqual(precision(cf), Decimal('1'))
        cf['tp'] = 0
        cf['fp'] = 0
        self.assertEqual(precision(cf), Decimal('0'))
        
    def test_recall(self):
        '''
        Test recall.
        '''
        cf = {}
        cf['tp'] = 1
        cf['fn'] = 1
        self.assertEqual(recall(cf), Decimal('0.5'))
        cf['tp'] = 1
        cf['fn'] = 3
        self.assertEqual(recall(cf), Decimal('0.25'))
        cf['tp'] = 6
        cf['fn'] = 2
        self.assertEqual(recall(cf), Decimal('0.75'))
        cf['tp'] = 0
        cf['fn'] = 2
        self.assertEqual(recall(cf), Decimal('0'))
        cf['tp'] = 2
        cf['fn'] = 0
        self.assertEqual(recall(cf), Decimal('1'))
        cf['tp'] = 0
        cf['fn'] = 0
        self.assertEqual(recall(cf), Decimal('0'))
        
    def test_f1(self):
        '''
        Test F-Score with a beta of 1.0, 0.5, or 2.0.
        '''
        cf = {}
        cf['tp'] = 2
        cf['fp'] = 1
        cf['fn'] = 1
        beta = 1.0
        self.assertEqual(fmeasure(cf, beta),
                         Decimal('4') / Decimal('6'))
        cf['tp'] = 1
        cf['fp'] = 3
        cf['fn'] = 1
        beta = 1.0
        self.assertEqual(fmeasure(cf, beta),
                         Decimal('1') / Decimal('3'))
        beta = 0.5
        self.assertAlmostEqual(fmeasure(cf, beta),
                               Decimal('0.277777777'))
        beta = 2.0
        self.assertAlmostEqual(fmeasure(cf, beta),
                               Decimal('0.416666666'))
        cf['tp'] = 0
        cf['fp'] = 0
        cf['fn'] = 0
        beta = 1.0
        self.assertEqual(fmeasure(cf, beta), Decimal('0'))
        
    def test_vars_to_cf(self):
        '''
        Tests converting variables into a confusion matrix.
        '''
        self.assertEqual(vars_to_cf(1, 2, 3, 4),
                         {'tp' : 1, 'fp' : 2, 'fn' : 3, 'tn' : 4})
        
    
    def test_cf_to_vars(self):
        '''
        Tests converting a confusion matrix into variables.
        '''
        self.assertEqual(cf_to_vars({'tp' : 1, 'fp' : 2, 'fn' : 3, 'tn' : 4}),
                         (1, 2, 3, 4))
