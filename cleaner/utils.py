
import numpy as np
from constants import DfConstants


class ColumnFinder:
    '''Class containing reusable function to find the USABLE column names, like T-C-F'''

    def df_column_finder(df):
        '''Gets column indices based on keywords of desired parameters T/C/F
        INPUT: dataframe
        OUTPUT: list of column # which contain the desired keywords'''

        lowercase_columns = df.columns.str.lower()

        time_column_index = np.where(lowercase_columns.str.contains(DfConstants.time_substring))[0][0]
        temp_column_index = np.where(lowercase_columns.str.contains(DfConstants.temperature_substring))[0][0]
        cond_column_index = np.where(lowercase_columns.str.contains(DfConstants.conductivity_substring))[0][0]
        flow_column_index = np.where(lowercase_columns.str.contains(DfConstants.flow_substring))[0][0]

        usable_columns_indices = [temp_column_index, cond_column_index, flow_column_index]

        return time_column_index, usable_columns_indices
