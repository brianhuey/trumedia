from pickle import load, dump
from run_expectancy import RunExpectancy
from heatmap import HeatMap

class Season(object):
    def __init__(self, basesFile, countFile, lastSeason=None):
        if lastSeason:
            self.season = load(open(lastSeason, 'r'))
        else:
            self.season = {}
        self.header = None
        self.runExp = RunExpectancy(basesFile, countFile)
        self.batterId, self.px, self.pz = None, None, None
        self.pitchType, self.pitchResult, self.paResult = None, None, None
        self.outs, self.balls, self.strikes = None, None, None
        self.first, self.second, self.third = None, None, None
        self.probCalledStrike, self.hand = None, None

    def process_batter(self, batterId, px, pz, pitchType, pitchResult,
                       paResult, hand):
        try:
            batterId = int(batterId)
            px, pz = float(px), float(pz)
        except:
            return
        if batterId in self.season:
            self.season[batterId].process_pitch(px, pz, pitchType, pitchResult,
                                                paResult, hand)
        else:
            self.season[batterId] = HeatMap()
            self.season[batterId].process_pitch(px, pz, pitchType, pitchResult,
                                                paResult, hand)

    def get_index(self, row, key):
        assert type(key) is str
        assert self.header
        return row[self.header.index(key)]

    def process_row(self, row):
        self.batterId = int(self.get_index(row, 'batterId'))
        try:
            self.px = float(self.get_index(row, 'px'))
            self.pz = float(self.get_index(row, 'pz'))
        except:
            raise ValueError('px and/or pz have no value')
        self.pitchType = str(self.get_index(row, 'pitchType'))
        self.pitchResult = str(self.get_index(row, 'pitchResult'))
        self.paResult = str(self.get_index(row, 'paResult'))
        self.outs = int(self.get_index(row, 'outs'))
        self.balls = int(self.get_index(row, 'balls'))
        self.strikes = int(self.get_index(row, 'strikes'))
        self.first = bool(self.get_index(row, 'manOnFirst') == 'TRUE')
        self.second = bool(self.get_index(row, 'manOnSecond') == 'TRUE')
        self.third = bool(self.get_index(row, 'manOnThird') == 'TRUE')
        self.probCalledStrike = float(self.get_index(row, 'probCalledStrike'))
        self.hand = str(self.get_index(row, 'pitcherHand'))

    def get_run_exp_prior_params(self):
        return (self.outs, self.balls, self.strikes, self.first, self.second,
                self.third)

    def get_run_exp_swing_params(self):
        heatMap = self.season[self.batterId]
        return (self.outs, self.balls, self.strikes, self.first, self.second,
                self.third, self.px, self.pz, self.pitchType, self.hand,
                heatMap)

    def get_run_exp_take_params(self):
        return (self.outs, self.balls, self.strikes, self.first, self.second,
                self.third, self.probCalledStrike)

    def get_process_batter_params(self):
        return (self.batterId, self.px, self.pz, self.pitchType,
                self.pitchResult, self.paResult, self.hand)

    def process_season(self, filename, output):
        """ Generate heat maps for a given CSV file. Outputs the heat maps
            objects pickled
        """
        with open(filename, 'r') as f:
            for num, line in enumerate(f):
                row = line.strip().split(',')
                if num == 0:
                    self.header = row
                else:
                    try:
                        self.process_row(row)
                    except ValueError:
                        continue
                    paramsBatter = self.get_process_batter_params()
                    self.process_batter(*paramsBatter)
        dump(self.season, open(output, 'w'))
        f.close()

    def generate_new_cols(self):
        """ Generate runExpPrior, runExpSwing, runExpTake
        """
        paramsPrior = self.get_run_exp_prior_params()
        runExpPrior = self.runExp.exp_runs(*paramsPrior)
        try:
            if self.batterId in self.season and self.outs < 3:
                paramsSwing = self.get_run_exp_swing_params()
                runExpSwing = self.runExp.exp_runs_swing(*paramsSwing)
                paramsTake = self.get_run_exp_take_params()
                runExpTake = self.runExp.exp_runs_take(*paramsTake)
            else:
                runExpSwing = ''
                runExpTake = ''
        except ZeroDivisionError:
            runExpSwing = ''
            runExpTake = ''
        return [str(runExpPrior), str(runExpSwing), str(runExpTake)]

    def process_file(self, filename, output):
        """ Processes play-by-play file generating/updating heat maps and run
            expectancy probabilities at each point in time.
            Output: original CSV file with appended run expectancies.
        """
        out = open(output, 'wa')
        with open(filename, 'r') as f:
            for num, line in enumerate(f):
                row = line.strip().split(',')
                if num == 0:
                    # Get header, create new column names
                    self.header = row
                    row += ['runExpPrior', 'runExpSwing', 'runExpTake\n']
                else:
                    try:
                        self.process_row(row)
                    except ValueError:
                        continue
                    row += self.generate_new_cols()
                    paramsBatter = self.get_process_batter_params()
                    self.process_batter(*paramsBatter)
                out.write(','.join(row) + '\n')
        f.close()
        out.close()
