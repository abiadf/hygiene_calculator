'''This module contains functions that find the absolute and relative extrema of dY, the derivative'''

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from constants import DfConstants
from data_cleaner import DataCleaner, DerivativeMaker
from utils import ColumnFinder


class FindDerivativePeaks():
    '''Class that gets the peaks given a dataframe of the data
    INPUT:
        - input_array: array of the desired property
        - comparison_order: how many points before/after a point do we use to determine it is a local min/max? 30 is a nice value
    OUTPUT:
        - dY_relative_max_idx: index of local maxima
        - dY_relative_min_idx: index of local minima
        - dY_max_idx: index of absolute maximum'''

    def __init__(self, df: pd.core.frame.DataFrame):
        self.df = df

    # remove below function if not used
    def setup(self):
        dYdx, _           = DataCleaner.make_derivatives(self.df) # Get derivatives
        lowercase_columns = dYdx.columns.str.lower()

        time_column_idx   = np.where(lowercase_columns.str.contains(DfConstants.time_substring))[0][0]
        temp_column_index = np.where(lowercase_columns.str.contains(DfConstants.temperature_substring))[0][0]
        cond_column_index = np.where(lowercase_columns.str.contains(DfConstants.conductivity_substring))[0][0]
        flow_column_index = np.where(lowercase_columns.str.contains(DfConstants.flow_substring))[0][0]

        usable_columns    = [temp_column_index, cond_column_index, flow_column_index]
        return time_column_idx, usable_columns


    def find_dY_absolute_extrema(self):
        '''This function get the ABSOLUTE extrema points from the derivative (dY) dataframe, for each parameter (T, C, F)
        input: -
        output: properties_df, which is a list of dictionaries, each dictionary dealing with a parameter'''

        dYdx_df, _                     = DerivativeMaker.make_derivatives(self.df) # Get derivatives
        time_column_idx, usable_columns= ColumnFinder.df_column_finder(dYdx_df) #FindDerivativePeaks.setup(self)
        list_of_properties_dict: list  = [] # List to store dicts for each parameter

        for _, val in enumerate(usable_columns):
            # Get absolute maximum dY and its location
            dY_max_value= np.amax(dYdx_df.iloc[:, val])
            dY_max_idx  = np.where(dYdx_df == dY_max_value)[0][0]   # dYdx_df.iloc[:, val].idxmax()
            dY_max_time = self.df.iloc[dY_max_idx, time_column_idx] # df[dYdx == dY_max_value].index[0]

            # Get absolute minimum dY and its location
            dY_min_value= np.amin(dYdx_df.iloc[:, val])
            dY_min_idx  = np.where(dYdx_df == dY_min_value)[0][0]
            dY_min_time = self.df.iloc[dY_min_idx, time_column_idx]

            dY_extrema_dict: dict = {'dY_max value':    dY_max_value,
                                     'dY_max idx [#]':  dY_max_idx,
                                     'dY_max time [s]': dY_max_time,
                                     'dY_min value':    dY_min_value,
                                     'dY_min idx [#]':  dY_min_idx,
                                     'dY_min time [s]': dY_min_time, }
            
            list_of_properties_dict.append(dY_extrema_dict)

        return list_of_properties_dict


    def find_dY_relative_extrema(self, comparison_order: int = 30) -> list:
        '''This function aims to get the RELATIVE extrema points from the derivative (dY) dataframe, for each parameter (T, C, F)
        INPUT: comparison_order, which is the # of neighboring points we compare to when deciding if we have a relative min/max
        OUTPUT: list_of_properties_df, a list of dictionaries, where each dictionary deals with a parameter'''

        dYdx_df, _                     = DerivativeMaker.make_derivatives(self.df) # Get derivatives
        time_column_idx, usable_columns= ColumnFinder.df_column_finder(dYdx_df)
        list_of_properties_df: list    = []  # List to store the dataframes

        for _, val in enumerate(usable_columns):
            # When does the normal curve begin to drastically change? When its derivative changes
            dY_relative_max_idx     = argrelextrema(dYdx_df.iloc[:, val].values, np.greater, order = comparison_order)[0]  #it is offset due to differentiation
            dY_relative_min_idx     = argrelextrema(dYdx_df.iloc[:, val].values, np.less,    order = comparison_order)[0]

            dY_relative_max_time    = self.df.iloc[dY_relative_max_idx, time_column_idx] #df.index[dY_relative_max_idx]
            dY_relative_min_time    = self.df.iloc[dY_relative_min_idx, time_column_idx]

            dY_relative_max_value   = dYdx_df.values[dY_relative_max_idx, val] #dYdx.iloc[dY_relative_max_idx, 1]
            dY_relative_min_value   = dYdx_df.values[dY_relative_min_idx, val]

            df_dY_relative_min_idx  = pd.DataFrame(dY_relative_min_idx,         columns = ['Index of rel min'])
            df_dY_relative_min_time = pd.DataFrame(dY_relative_min_time.values, columns = ['Time of rel min'])
            df_dY_relative_min_value= pd.DataFrame(dY_relative_min_value,       columns = ['Rel min value'])
            df_dY_relative_max_idx  = pd.DataFrame(dY_relative_max_idx,         columns = ['Index of rel max'])
            df_dY_relative_max_time = pd.DataFrame(dY_relative_max_time.values, columns = ['Time of rel max'])
            df_dY_relative_max_value= pd.DataFrame(dY_relative_max_value,       columns = ['Rel max value'])

            df_dY_relative_extrema  = pd.concat([df_dY_relative_min_idx, df_dY_relative_min_time, df_dY_relative_min_value,
                                                 df_dY_relative_max_idx, df_dY_relative_max_time, df_dY_relative_max_value,],
                                                 axis = 1)

            df_dY_relative_extrema_no_NaN     = df_dY_relative_extrema.replace(np.nan, 0.0)
            df_dY_relative_extrema_no_NaN_NaT = df_dY_relative_extrema_no_NaN.replace(pd.NaT, 0.0)

            list_of_properties_df.append(df_dY_relative_extrema_no_NaN_NaT)

        # print(list_of_properties_df[0].loc[:, 'Index of rel min'])
        # print(list_of_properties_df[0].loc[:, 'Index of rel max'])
        # print((list_of_properties_df))

        # from sys import exit
        # exit()

        return list_of_properties_df
