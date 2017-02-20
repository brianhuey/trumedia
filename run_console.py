import pandas as pd
from batters import Batters

def create_df(filename):
    df = pd.read_csv(filename)
    cols = ['batter', 'batterId', 'probCalledStrike', 'runExpPrior',
            'runExpSwing', 'runExpTake', 'pitchResult', 'paResult']
    df = df[cols]
    swings = ['IP', 'SS', 'F', 'FT', 'MB']
    takes = ['B', 'SL', 'BID']
    df['swing'] = df['pitchResult'].isin(swings)
    df['take'] = df['pitchResult'].isin(takes)
    df['shouldSwing'] = df['runExpSwing'] > df['runExpTake']
    df['dSwing'] = df['runExpSwing'] - df['runExpPrior']
    df['shouldTake'] = df['runExpSwing'] < df['runExpTake']
    df['dTake'] = df['runExpTake'] - df['runExpPrior']
    df['dSwingTake'] = df['runExpSwing'] - df['runExpTake']
    return df

csv = 'data/2016_processed.csv'
df = create_df(csv)

batters = Batters(df, minPA=500)

def create_leaderboard(name, df, n, top=True, ascending=True):
    if top:
        filename = 'leaderboard/' + name + '_top_%s.csv' % (n)
    else:
        filename = 'leaderboard/' + name + '_bottom_%s.csv' % (n)
    (df.set_index('batter_name')[name].sort_values(ascending=ascending).
     head(n).to_csv(filename))
