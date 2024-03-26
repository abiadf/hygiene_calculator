
from dataclasses import dataclass
import numpy as np

from data_cleaner import DataCleaner
# from run_tempKPI_derivative import temp_abs_extrema, dY_relative_extrema, dY_absolute_extrema, df_smooth
# from multi_file_maker import temp_abs_extrema, dY_relative_extrema, dY_absolute_extrema, df_smooth
from utils import ColumnFinder


'''Class to store variables'''

df_example = df_smooth.copy()

@dataclass
class Variables():       
    '''Place to store variables to use throughout the code'''

    df      = df_example

    dYdx, _ = DataCleaner.make_derivatives(df) # Get derivatives
    time_column_idx, usable_columns= ColumnFinder.df_column_finder(dYdx)
    
    t_column_index = 0
    T_column_index = 1
    C_column_index = 2
    F_column_index = 3

    df_indices= df.index.to_series()
    t_values  = df.iloc[:, t_column_index]
    T_values  = df.iloc[:, T_column_index]
    C_values  = df.iloc[:, C_column_index]
    F_values  = df.iloc[:, F_column_index]

    parameters_dict = {'t': t_values, \
                       'T': T_values, \
                       'C': C_values, \
                       'F': F_values, }

    dT_values = dYdx.iloc[:, T_column_index]
    dC_values = dYdx.iloc[:, C_column_index]
    dF_values = dYdx.iloc[:, F_column_index]

    dT_idx = 0 #index of dY temperature column in array
    dC_idx = 1 #index of dY conductivity column in array
    dF_idx = 2 #index of dY flow column in array

    relative_min_index_idx= 0
    relative_min_time_idx = 1
    relative_max_index_idx= 3
    relative_max_time_idx = 4

    dT_rel_max_idx = dY_relative_extrema[dT_idx].iloc[:, relative_max_index_idx]
    dT_rel_min_idx = dY_relative_extrema[dT_idx].iloc[:, relative_min_index_idx]
    dT_max_idx     = dY_absolute_extrema[dT_idx]['dY_max idx [#]']

    dC_rel_max_idx = dY_relative_extrema[dC_idx].iloc[:, relative_max_index_idx]
    dC_max_idx     = dY_absolute_extrema[dC_idx]['dY_max idx [#]']

    dF_rel_max_idx = dY_relative_extrema[dF_idx].iloc[:, relative_max_index_idx]
    dF_max_idx     = dY_absolute_extrema[dF_idx]['dY_max idx [#]']


    dT_relative_max_time = dY_relative_extrema[dT_idx].iloc[:, relative_max_time_idx]
    dT_relative_min_time = dY_relative_extrema[dT_idx].iloc[:, relative_min_time_idx]
    
    dC_relative_max_time = dY_relative_extrema[dC_idx].iloc[:, relative_max_time_idx]
    dC_relative_min_time = dY_relative_extrema[dC_idx].iloc[:, relative_min_time_idx]

    dF_relative_max_time = dY_relative_extrema[dF_idx].iloc[:, relative_max_time_idx]
    dF_relative_min_time = dY_relative_extrema[dF_idx].iloc[:, relative_min_time_idx]

    dT_max_value = dY_absolute_extrema[dT_idx]['dY_max value']
    dT_max_time  = dY_absolute_extrema[dT_idx]['dY_max time [s]']

    T_max        = temp_abs_extrema['T_max [C]']
    T_max_time   = temp_abs_extrema['T_max time [s]']
    T_max_idx    = temp_abs_extrema['T_max idx [#]']

    C_max        = np.amax(C_values)
    C_max_idx    = np.where(C_values == C_max)[0][0]
    C_max_time   = t_values[C_max_idx]

