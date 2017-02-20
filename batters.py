import pandas as pd
from numpy import mean

class Batters(object):
    def __init__(self, df, minPA=None):
        self.orig_df = df
        if minPA:
            self.batterIds = self.min_pa(df, minPA)
        else:
            self.batterIds = pd.unique(self.df['batterId'])
        self.df = df[df['batterId'].isin(self.batterIds)]

    def min_pa(self, df, minPA):
        df_group = (df[df['paResult'].isnull() == False].groupby('batterId')
                    ['paResult'].agg(len))
        return list(df_group[df_group >= minPA].index)

    def get_swing_value_added(self):
        """ Returns group by object of pitches where batter swung when it
            was optimal to do so.
        """
        df = self.df[(self.df['swing'] == True) & (self.df['shouldSwing'] ==
                                                   True)]
        return df.groupby('batter')['dSwing']

    def get_swing_value_lost(self):
        """ Returns group by object of pitches where batter swung when it
            was sub-optimal to do so.
        """
        df = self.df[(self.df['swing'] == True) & (self.df['shouldSwing'] ==
                                                   False)]
        return df.groupby('batter')['dSwing']

    def get_take_value_added(self):
        """ Returns group by object of pitches where batter took when it
            was optimal to do so.
        """
        df = self.df[(self.df['take'] == True) & (self.df['shouldTake'] ==
                                                   True)]
        return df.groupby('batter')['dTake']

    def get_take_value_lost(self):
        """ Returns group by object of pitches where batter took when it
            was sub-optimal to do so.
        """
        df = self.df[(self.df['take'] == True) & (self.df['shouldTake'] ==
                                                   False)]
        return df.groupby('batter')['dTake']

    def get_swing_value_total(self):
        df = self.df[((self.df['swing'] == True) &
                      (self.df['shouldSwing'] == True)) |
                      ((self.df['swing'] == True) &
                      (self.df['shouldSwing'] == False))]
        return df.groupby('batter')['dSwing']

    def get_take_value_total(self):
        df = self.df[((self.df['take'] == True) &
                      (self.df['shouldTake'] == True)) |
                      ((self.df['take'] == True) &
                      (self.df['shouldTake'] == False))]
        return df.groupby('batter')['dTake']

    def get_value_net_total(self):
        swing_df = self.df[((self.df['swing'] == True) &
                           (self.df['shouldSwing'] == True)) |
                           ((self.df['swing'] == True) &
                           (self.df['shouldSwing'] == False))]['dSwing']
        take_df = self.df[((self.df['take'] == True) &
                          (self.df['shouldTake'] == True)) |
                          ((self.df['take'] == True) &
                          (self.df['shouldTake'] == False))]['dTake']
        df = pd.concat([swing_df, take_df], axis=1)
        df = df.join(self.df['batter'])
        df['net_total'] = df['dSwing'].fillna(df['dTake'])
        return df.groupby('batter')['net_total']

    def create_full_dataframe(self):
        """ Returns data frame of the cumulative sum of all metrics
        """
        objs = [self.get_swing_value_added().agg(sum),
                self.get_swing_value_lost().agg(sum),
                self.get_take_value_added().agg(sum),
                self.get_take_value_lost().agg(sum),
                self.get_swing_value_total().agg(sum),
                self.get_take_value_total().agg(sum),
                self.get_value_net_total().agg(sum)]
        keys = ['dSwing|Swing', 'dSwing|Take', 'dTake|Take', 'dTake|Swing',
                'dSwing', 'dTake', 'NetTotal']
        df = pd.concat(objs, keys=keys, axis=1).round(2)
        return df

    def create_count_dataframe(self):
        """ Returns data frame of the cumulative count of all metrics
        """
        objs = [self.get_swing_value_added().agg(len),
                self.get_swing_value_lost().agg(len),
                self.get_take_value_added().agg(len),
                self.get_take_value_lost().agg(len),
                self.get_swing_value_total().agg(len),
                self.get_take_value_total().agg(len),
                self.get_value_net_total().agg(len)]
        keys = ['dSwing|Swing_count', 'dSwing|Take_count', 'dTake|Take_count',
                'dTake|Swing_count', 'dSwing_count', 'dTake_count',
                'NetTotal_count']
        df = pd.concat(objs, keys=keys, axis=1).round(2)
        df.columns = df.columns.droplevel(1)
        return df

    def create_mean_dataframe(self):
        """ Returns data frame of the mean of all metrics normalized per 100
            pitches
        """
        objs = [self.get_swing_value_added().agg(mean) * 100,
                self.get_swing_value_lost().agg(mean) * 100,
                self.get_take_value_added().agg(mean) * 100,
                self.get_take_value_lost().agg(mean) * 100,
                self.get_swing_value_total().agg(mean) * 100,
                self.get_take_value_total().agg(mean) * 100,
                self.get_value_net_total().agg(mean) * 100]
        keys = ['dSwing|Swing_mean', 'dSwing|Take_mean', 'dTake|Take_mean',
                'dTake|Swing_mean', 'dSwing_mean', 'dTake_mean',
                'NetTotal_mean']
        df = pd.concat(objs, keys=keys, axis=1).round(4)
        return df