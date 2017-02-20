from pandas import read_csv
from numpy import mean
from pickle import dump, load

class RunExpectancy(object):
    def __init__(self, bases_file, count_file):
        self.runExpCount = load(open(count_file, 'r'))
        self.runExpBases = load(open(bases_file, 'r'))
        # These values are for bitwise operations
        self.hits = {'S': 1, 'D': 2, 'T': 4, 'HR': 8}

    def exp_runs(self, outs, balls, strikes, first, second, third):
        """ Returns the expected runs from the inning at a given point
            during an at bat.
        """
        if outs == 3:
            return 0
        else:
            return self.runExpCount[outs, balls, strikes, first, second, third]

    def strike_outcomes(self, outs, balls, strikes, first, second, third):
        if outs == 2:
            if strikes == 2:
                # Strikeout, inning over
                return 0
            else:
                strikes += 1
        else:
            if strikes == 2:
                # Strikeout, at-bat over
                outs += 1
                strikes = 0
                balls = 0
            else:
                strikes += 1
        return self.exp_runs(outs, balls, strikes, first, second, third)

    def ball_outcomes(self, outs, balls, strikes, first, second, third):
        runs = 0
        if balls == 3:
            first = True
            if first and second and third:
                # Bases loaded walk, score
                runs = 1.0
            elif first and second:
                # Walk, bases loaded
                third = True
            elif first:
                # Walk, runners on first and second
                second = True
        else:
            balls += 1
        return runs + self.exp_runs(outs, balls, strikes, first, second, third)

    def out_outcomes(self, outs, balls, strikes, first, second, third):
        if outs == 2:
            # Out, inning over
            return 0
        else:
            outs += 1
        return self.exp_runs(outs, balls, strikes, first, second, third)

    def foul_outcomes(self, outs, balls, strikes, first, second, third):
        if strikes < 2:
            strikes += 1
        return self.exp_runs(outs, balls, strikes, first, second, third)

    def adjust_runners(self, first, second, third, runs, hit):
        """ Adjust base runners to reflect the hit and the number of runs
            scored using bitwise operations.
        """
        if hit == 'HR':
            return [False, False, False]
        r = [0, 8, 24, 56, 120]
        occupied = sum([x*y for x, y in zip([4, 2, 1], [third, second,
                                                        first])])
        base = self.hits[hit]
        scored = 0
        for shift in range(4):
            newOccupied = occupied << shift
            if newOccupied == r[runs + 1]:
                raise ValueError('Parameter values are illogical')
            # First make sure the correct number of runs score
            if newOccupied & 8 == 8:
                scored += 1
            if r[scored] == r[runs]:
                # Second make sure the batter is trailing the base runners
                if newOccupied & base == base:
                    if newOccupied & base*2 == base*2:
                        # Advance both lead runners one base
                        newOccupied += base * 2 * 2
                    else:
                        # Advance the lead runner one base
                        newOccupied += base * 2
                else:
                    newOccupied += base
                newOccupied = bin(newOccupied & ~r[4])[2:]
                padding = 3 - len(newOccupied)
                newOccupied = '0' * padding + newOccupied
                return [bool(newOccupied[x] == '1') for x in
                        reversed(range(3))]
        raise BaseException('Could not adjust runners in a logical manner')

    def base_outcomes(self, outs, balls, strikes, first, second, third, hit):
        assert hit in self.hits
        runs = self.runExpBases[hit, first, second, third, outs]
        bases = self.adjust_runners(first, second, third, int(round(runs, 0)),
                                    hit)
        count = self.exp_runs(outs, 0, 0, *bases)
        return runs + count

    def exp_runs_swing(self, outs, balls, strikes, first, second, third,
                       px, pz, pitchType, hand, heatmap):
        """ Returns the expected runs from the inning given the batter
            swings at the pitch.
            P(single|swing) * runExp(single)
            P(double|swing) * runExp(double)
            P(triple|swing) * runExp(triple)
            P(homer|swing) * runExp(homer)
            P(miss|swing) * runExp(miss)
            P(out|swing) * runExp(out)
            P(foul|swing) * runExp(foul)
        """
        s = self.base_outcomes(outs, balls, strikes, first, second,
                                  third, 'S')
        single = heatmap.prob_single(px, pz, pitchType, hand) * s
        d  = self.base_outcomes(outs, balls, strikes, first, second,
                                   third, 'D')
        double = heatmap.prob_double(px, pz, pitchType, hand) * d
        t = self.base_outcomes(outs, balls, strikes, first, second,
                                  third, 'T')
        triple = heatmap.prob_double(px, pz, pitchType, hand) * t
        hr = self.base_outcomes(outs, balls, strikes, first, second,
                                   third, 'HR')
        homer = heatmap.prob_homer(px, pz, pitchType, hand) * hr
        miss = heatmap.prob_miss(px, pz, pitchType, hand) * \
                 self.strike_outcomes(outs, balls, strikes, first, second,
                                      third)
        out = heatmap.prob_out(px, pz, pitchType, hand) * \
                 self.out_outcomes(outs, balls, strikes, first, second,
                                      third)
        foul = heatmap.prob_foul(px, pz, pitchType, hand) * \
                 self.foul_outcomes(outs, balls, strikes, first, second,
                                      third)
        run_exp = sum([single, double, triple, homer, miss, out, foul])
        return run_exp


    def exp_runs_take(self, outs, balls, strikes, first, second, third,
                         probCalledStrike):
        """ Returns the expected runs from the inning given the batter
            takes the pitch.
        """
        probStrike = probCalledStrike
        probBall = 1 - probStrike
        strikeRuns = self.strike_outcomes(outs, balls, strikes, first, second,
                                          third)
        ballRuns = self.ball_outcomes(outs, balls, strikes, first, second,
                                      third)
        return (probStrike*strikeRuns) + (probBall * ballRuns)

# Generate run expectancy tables
def run_expectancy_count(filename, output=False):
    """ Create Run Expectancies based on count from play-by-play file
        Input: filename
        Output: pickled pandas dataframe
    """
    df = read_csv(filename)
    df['runsHome'].fillna(0, inplace=True)
    runs = df.groupby(['gameString', 'inning', 'side'])['runsHome'].agg(sum)
    df_runs = df.apply(lambda x: runs[x['gameString'], x['inning'], x['side']],
                       axis=1)
    df_runs.name = 'runs'
    df = df.join(df_runs)
    df_min = df[['outs', 'balls', 'strikes', 'manOnFirst', 'manOnSecond',
                'manOnThird', 'runs']]
    run_exp = df_min.groupby(['outs', 'balls', 'strikes', 'manOnFirst',
                              'manOnSecond', 'manOnThird'])['runs'].agg(mean)
    if output:
        assert type(output) is str
        dump(run_exp, open(output, 'w'))
    else:
        return run_exp

def run_expectancy_hits(filename, output=False):
    """ Create Run Expectancies based on hits from play-by-play file
        Input: filename
        Output: pickled pandas dataframe
    """
    hits = ['S', 'D', 'T', 'HR']
    df = read_csv(filename)
    df['runsHome'].fillna(0, inplace=True)
    df_hits = df[df['paResult'].isin(hits) == True]
    run_exp = df_hits.groupby(['paResult', 'manOnFirst', 'manOnSecond',
                               'manOnThird', 'outs'])['runsHome'].agg(mean)
    run_exp.fillna(0, inplace=True)
    if output:
        assert type(output) is str
        dump(run_exp, open(output, 'w'))
    else:
        return run_exp