import unittest
from heatmap import HeatMap
from run_expectancy import RunExpectancy
from pickle import load

run_exp_hits = '../data/run_exp_hits_2015.pickle'
run_exp_count = '../data/run_exp_count_2015.pickle'
test_data = 'test_data.pickle'

class Heatmap_unittest(unittest.TestCase):
    def setUp(self):
        self.rows = load(open(test_data, 'r'))
        self.heatmap = HeatMap()
        for idx in range(5):
            params = self.rows[idx]
            self.heatmap.process_pitch(*params)

    def test_keys(self):
        """ Test keys are correct.
        """
        keys = self.heatmap.maps['R'].keys()
        key_answer = ['SI', 'SL']
        self.assertItemsEqual(key_answer, keys)

    def test_add(self):
        """ Test incremental adding
        """
        # Out recorded
        self.heatmap.process_pitch(*self.rows[12])
        first = self.heatmap.maps['R']['SI'][5,2,3]
        self.assertEqual(first, 1)
        # Add same pitch
        self.heatmap.process_pitch(*self.rows[12])
        second = self.heatmap.maps['R']['SI'][5,2,3]
        self.assertEqual(second, 2)

    def test_prob(self):
        foul = self.heatmap.prob_foul(0.647, 2.325, 'SL', 'R')
        answer = 1.0
        self.assertEqual(foul, answer)
        # Add new pitch, should increment swings, changing probability
        self.heatmap.process_pitch(0.647, 2.325, 'SL', 'SS', '', 'R')
        foul = self.heatmap.prob_foul(0.647, 2.325, 'SL', 'R')
        answer = 0.5
        self.assertEqual(foul, answer)

class RunExp_unittest(unittest.TestCase):
    def setUp(self):
        self.runExp = RunExpectancy(run_exp_hits, run_exp_count)

    def test_adjust_runners_basehit(self):
        # Runners first, third, one run scores
        first, second, third = True, False, True
        runs, hit = 1, 'D'
        runners = self.runExp.adjust_runners(first, second, third, runs, hit)
        # Runners on second and third
        answer = [False, True, True]
        self.assertListEqual(runners, answer)
        # Runners on first, second no runs score
        first, second, third = True, True, False
        runs, hit = 0, 'S'
        runners = self.runExp.adjust_runners(first, second, third, runs, hit)
        # Runners on first, second, third
        answer = [True, True, True]
        self.assertListEqual(runners, answer)

    def test_adjust_runners_hr(self):
        # Runner on second, home run
        first, second, third = False, True, False
        runs, hit = 2, 'HR'
        runners = self.runExp.adjust_runners(first, second, third, runs, hit)
        answer = [False, False, False]
        self.assertListEqual(runners, answer)

