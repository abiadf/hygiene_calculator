'''Make TemperatureKPIObtainer() class'''

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from config_info_obtainer import Constants
from constants import DfConstants
from logging_maker import logger


class TemperatureKPIObtainer():
    '''Gets relative and absolute points of TEMPERATURE T, because temperature has lots of KPIs associated with it
    INPUT:
        - df: input dataframe
        - comparison_order: points to consider on each side of comparison to determine whether point is relative min/max, 30 is a good value
    OUTPUT: dictionary of relative points'''
    
    def __init__(self, df: pd.core.frame.DataFrame):
        self.df = df
        self.time_column_idx = 0  # should be 0 (or the DataFrame index) usually


    def make_temperature_df(self):
        '''Setup function that takes the input DataFrame (df) and outputs a df of temperature and its column #
        INPUT: Standard df
        OUTPUT: df consisting of only the time and temperature points'''

        lowercase_columns = self.df.columns.str.lower()
        where_is_t_column = np.where(lowercase_columns.str.contains(DfConstants.time_substring))[0][0]
        if self.time_column_idx != where_is_t_column:
            logger.warning(f"The time column index (#{where_is_t_column}) is different than the expected column (#{self.time_column_idx})")

        temp_column_index = np.where(lowercase_columns.str.contains(DfConstants.temperature_substring))[0][0]
        temp_df           = self.df.iloc[:, :temp_column_index + 1]

        return temp_df, temp_column_index


    def calculate_temperature_relative_extrema(self, comparison_order: int = 30) -> pd.core.frame.DataFrame:
        '''Calculates the extrema points of temperature, like local minima and maxima
        OUTPUT: df_temp_extrema, which is a DataFrame of Temperature extrema points'''

        temp_df, _           = TemperatureKPIObtainer.make_temperature_df(self)

        relative_min_idx     = argrelextrema(temp_df.values, np.less,    order = comparison_order)[0]
        relative_max_idx     = argrelextrema(temp_df.values, np.greater, order = comparison_order)[0]
        relative_min_time    = temp_df.iloc[relative_min_idx, self.time_column_idx]
        relative_max_time    = temp_df.iloc[relative_max_idx, self.time_column_idx]
        relative_min_values  = temp_df.iloc[relative_min_idx, -1] #temp is at last column
        relative_max_values  = temp_df.iloc[relative_max_idx, -1] #temp is at last column

        df_relative_min_idx  = pd.DataFrame(relative_min_idx,           columns=['Rel min index'])
        df_relative_max_idx  = pd.DataFrame(relative_max_idx,           columns=['Rel max index'])
        df_relative_min_time = pd.DataFrame(relative_min_time.values,   columns=['Time of rel min'])
        df_relative_max_time = pd.DataFrame(relative_max_time.values,   columns=['Time of rel max'])
        df_relative_min_value= pd.DataFrame(relative_min_values.values, columns=['Value of rel min'])
        df_relative_max_value= pd.DataFrame(relative_max_values.values, columns=['Value of rel max'])

        df_temp_extrema      = pd.concat([df_relative_min_idx, df_relative_min_time, df_relative_min_value,
                                          df_relative_max_idx, df_relative_max_time, df_relative_max_value,],
                                          axis = 1)
        return df_temp_extrema


    def calculate_temperature_absolute_extrema(self) -> dict:
        '''Obtains the temperature keypoints
        Output: dictionary containing key temperature values like T_max and 2-min window wiht highest T'''

        temp_df, temp_column_index = TemperatureKPIObtainer.make_temperature_df(self)

        temp_column       = self.df.iloc[:, temp_column_index]
        T_max_value       = np.amax(temp_column)
        T_max_idx         = np.where(temp_column == T_max_value)[0][0]
        time_column_index = self.df.columns.get_loc(DfConstants.df_time_column)
        T_max_time        = temp_df.iloc[T_max_idx, time_column_index]

        T_criterion           = Constants.T_crit # set in the config file
        T_above_crit_idx      = np.where(temp_column > T_criterion)[0] # Temperature values above the crit
        T_above_crit_duration = len(T_above_crit_idx)              # time [s] where T > T_criterion (set in config file)

        # Get "avg. T of time interval with highest T [C]"
        time_interval_window       = Constants.time_interval
        T_moving_avg_time_interval = temp_column.rolling(time_interval_window).mean()
        T_of_max_time_interval     = np.amax(T_moving_avg_time_interval)

        max_temp_keypoints = {'T_max [C]':                          T_max_value,
                              'T_max idx [#]':                      T_max_idx,
                              'T_max time [s]':                     T_max_time,
                              'Index of T values above T_crit [#]': T_above_crit_idx,
                              'Duration for which T > T_crit [s]':  T_above_crit_duration,
                              'T of max time interval [C]':         T_of_max_time_interval, }

        return max_temp_keypoints
