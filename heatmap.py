import numpy as np

class HeatMap(object):
    def __init__(self):
        self.maps = {'L': {}, 'R': {}}
        self.xs = [-0.708, -0.236, 0.236, 0.708, np.inf]
        self.zs = [1.5, 2.5, 3.5, 4.5, np.inf]
        self.bases = {'K': 0, 'IP_OUT': 0, 'S': 1, 'HR': 4, 'D': 2, 'DP': 0,
                      'T': 3, 'ROE': 0, 'FC': 0, 'SH': 0, 'SF': 0, 'HBP': 0,
                      'IBB': 0, 'BB': 0, 'TP': 0, 'SH_ROE': 0, 'SF_ROE': 0,
                      'BI': 0, 'CI': 0, 'FI': 0, 'NO_PLAY': 0}
        self.misses = {'SS'}
        self.outs = {'K': 0, 'IP_OUT': 1, 'DP': 2, 'TP': 3, 'FC': 1, 'SH': 1,
                     'SF': 1}
        self.swings = {'SS', 'F', 'FT', 'IP'}
        self.fouls = {'F', 'FT'}
        # Ignore hbp, intentional walk, interference, automatic ball/strike
        self.ignorePitchResults = {'HBP', 'IB', 'AS', 'AB', 'CI', 'UK'}
        # Ignore pitchout, intentional ball, automatic ball/strike
        self.ignorePitchTypes = {'PO', 'IN', 'AB', 'AS', 'UN'}
        # Ignore interference, no play
        self.ignorePaResults = {'BI', 'CI', 'FI', 'NO_PLAY'}
        self.S, self.D, self.T, self.HR = 0, 1, 2, 3
        self.miss, self.out, self.foul, self.swing, self.total = 4, 5, 6, 7, 8

    def generate_new_map(self):
        """ Generate nine 5 x 5 heat maps:
            0) total singles
            1) total doubles
            2) total triples
            3) total home runs
            4) total swings and misses
            5) total ip outs
            6) total fouls
            7) total swings
            8) total pitches seen
        """
        return np.zeros((9, 5, 5), dtype=int)

    def add_single(self, i, j, pitchType, paResult, hand):
        self.maps[hand][pitchType][self.S, i, j] += 1

    def add_double(self, i, j, pitchType, paResult, hand):
        self.maps[hand][pitchType][self.D, i, j] += 1

    def add_triple(self, i, j, pitchType, paResult, hand):
        self.maps[hand][pitchType][self.T, i, j] += 1

    def add_homer(self, i, j, pitchType, paResult, hand):
        self.maps[hand][pitchType][self.HR, i, j] += 1

    def add_miss(self, i, j, pitchType, hand):
        self.maps[hand][pitchType][self.miss, i, j] += 1

    def add_out(self, i, j, pitchType, paResult, hand):
        self.maps[hand][pitchType][self.out, i, j] += self.outs[paResult]

    def add_foul(self, i, j, pitchType, hand):
        self.maps[hand][pitchType][self.foul, i, j] += 1

    def add_swing(self, i, j, pitchType, hand):
        self.maps[hand][pitchType][self.swing, i, j] += 1

    def add_total(self, i, j, pitchType, hand):
        self.maps[hand][pitchType][self.total, i, j] += 1

    def get_location(self, px, pz):
        """ For a given pitch coordinate, return its location in the zone map.
        """
        i = 4 - list(np.less_equal(pz, self.zs)).index(True)
        j = list(np.less_equal(px, self.xs)).index(True)
        return i, j

    def process_pitch(self, px, pz, pitchType, pitchResult, paResult, hand):
        """ Input pitchfx data and use it to update heat maps
        """
        if ((pitchType in self.ignorePitchTypes) or
            (pitchResult in self.ignorePitchResults) or
            (paResult in self.ignorePaResults)):
            return None
        if pitchType not in self.maps[hand]:
            self.maps[hand][pitchType] = self.generate_new_map()
        i, j = self.get_location(px, pz)
        self.add_total(i, j, pitchType, hand)
        if pitchResult in self.swings:
            self.add_swing(i, j, pitchType, hand)
        if pitchResult in self.fouls:
            self.add_foul(i, j, pitchType, hand)
        elif pitchResult in self.misses:
            self.add_miss(i, j, pitchType, hand)
        if paResult in self.outs:
            self.add_out(i, j, pitchType, paResult, hand)
        elif paResult == 'S':
            self.add_single(i, j, pitchType, paResult, hand)
        elif paResult == 'D':
            self.add_double(i, j, pitchType, paResult, hand)
        elif paResult == 'T':
            self.add_triple(i, j, pitchType, paResult, hand)
        elif paResult == 'HR':
            self.add_homer(i, j, pitchType, paResult, hand)

    def get_value(self, px, pz, pitchType, idx, hand):
        try:
            i, j = self.get_location(px, pz)
            value = self.maps[hand][pitchType][idx, i, j]
            return float(value)
        except KeyError:
            return float(0)

    def prob_single(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(base|swing)
        """
        singles = self.get_value(px, pz, pitchType, self.S, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return singles / swings

    def prob_double(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(base|swing)
        """
        doubles = self.get_value(px, pz, pitchType, self.D, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return doubles / swings

    def prob_triple(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(base|swing)
        """
        triples = self.get_value(px, pz, pitchType, self.T, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return triples / swings

    def prob_homer(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(base|swing)
        """
        homers = self.get_value(px, pz, pitchType, self.HR, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return homers / swings

    def prob_miss(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(miss|swing)
        """
        misses = self.get_value(px, pz, pitchType, self.miss, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return misses / swings

    def prob_out(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(out|swing)
        """
        outs = self.get_value(px, pz, pitchType, self.out, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return outs / swings

    def prob_foul(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(foul|swing)
        """
        fouls = self.get_value(px, pz, pitchType, self.foul, hand)
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        return fouls / swings

    def prob_swing(self, px, pz, pitchType, hand):
        """ Input pitch type and location
            Returns P(swing)
        """
        swings = self.get_value(px, pz, pitchType, self.swing, hand)
        totals = self.get_value(px, pz, pitchType, self.total, hand)
        return swings / totals