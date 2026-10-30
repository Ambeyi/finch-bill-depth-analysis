import unittest
import pandas as pd
from analyze import analyze

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({'daphne_all':[8,10,10,12,None,None], 'survive':[0,0,1,1,None,None], 'both_islands':[8,10,10,12,11,13], 'location':[0,0,0,0,1,1]})
    def test_known_means_and_denominators(self):
        table, metrics, _ = analyze(self.data)
        self.assertEqual(table.n.tolist(), [2,2,4,2])
        self.assertEqual(table['mean'].tolist(), [9,11,10,12])
        self.assertEqual(metrics['survival_fraction'], .5)
        self.assertEqual(metrics['survivor_minus_population_mean'], 1)
        self.assertAlmostEqual(table.iloc[0]['sd'], 2**.5)
    def test_padded_rows_are_not_observations(self):
        padded = pd.concat([self.data, pd.DataFrame([{c:float('nan') for c in self.data.columns}], dtype=float)])
        self.assertEqual(analyze(padded)[1], analyze(self.data)[1])
    def test_unpaired_missing_is_rejected(self):
        self.data.loc[0,'survive'] = None
        with self.assertRaises(ValueError): analyze(self.data)
    def test_invalid_values(self):
        for col,value in [('survive',2),('location',-1),('daphne_all',0),('both_islands',float('inf'))]:
            bad = self.data.astype(float).copy(); bad.loc[0,col] = value
            with self.subTest(col=col), self.assertRaises(ValueError): analyze(bad)
    def test_missing_columns_and_empty(self):
        for bad in [self.data.drop(columns='survive'), self.data.iloc[:0]]:
            with self.assertRaises(ValueError): analyze(bad)
    def test_singleton_group(self):
        with self.assertRaises(ValueError): analyze(self.data.iloc[:-1])

if __name__ == '__main__': unittest.main()
