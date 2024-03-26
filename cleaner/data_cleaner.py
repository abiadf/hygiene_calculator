'''Module dealing with cleaning the data, by filling gaps, smoothening data, then makes derivatives of the data, and clips these derivatives (if too sharp)'''

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

import matplotlib.pyplot as plt

from constants import DfConstants


class DataCleaner:
    '''Class that fills gaps in data and smoothens data'''

    def __init__(self):
        pass


    @staticmethod
    def fill_data_gaps(df: pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
        '''Fills the NaN gaps in data without removing entries
        Input: dataframe containing [time, T, C, F] data
        Output: dataframe without NaN values
        NOTE: Possibilities to close data gaps: ffill, bfill, dropna, interpolate (linear/spline/polynomial), fillna, fillna(mean), rolling'''

        df_filled        = df.copy()
        time_column_id   = df.columns.get_loc(DfConstants.df_time_column)
        number_of_columns= df_filled.shape[1]
       
        for i in range(time_column_id + 1, number_of_columns):
            # df_filled.iloc[:, i] = df.iloc[:, i].fillna(method = 'bfill') # deprecated pandas function
            df_filled.iloc[:, i] = df.iloc[:, i].bfill()

            # Handling NaN of a column's LAST value:
            if pd.isna(df_filled.iloc[-1, i]):
                last_non_null_value   = df_filled.iloc[:, i].dropna().iloc[-1]
                df_filled.iloc[-1, i] = last_non_null_value

        return df_filled


    @staticmethod
    def smoothen_data(df: pd.core.frame.DataFrame, window_size: int = 5) -> pd.core.frame.DataFrame:
        '''Smoothens the data per column (temp, cond, flow)
        INPUT: dataframe containing [time, T, C, F] data
        window_size: how big is the averaging window. Somewhere between 3-5 is good'''

        df_smooth        = df.copy()
        time_column_id   = df.columns.get_loc(DfConstants.df_time_column)
        number_of_columns= df_smooth.shape[1]

        for i in range(time_column_id + 1, number_of_columns):
            df_smooth.iloc[:, i] = df.iloc[:, i].rolling(window_size, min_periods = 1).mean()
            df_smooth_shifted    = df_smooth.shift(1 - window_size) # to counter the shift from rolling

        return df_smooth_shifted


    @staticmethod
    def _get_max_value_of_each_series(df: pd.core.frame.DataFrame):

        column_names_list = df.columns.tolist()

        temp_column_name  = [col for col in column_names_list if DfConstants.temperature_substring.lower() in col.lower()]
        temp_column_name  = temp_column_name[0]
        T_column_in_df    = df[temp_column_name]
        T_max_val         = np.amax(T_column_in_df)

        cond_column_name  = [col for col in column_names_list if DfConstants.conductivity_substring.lower() in col.lower()]
        cond_column_name  = cond_column_name[0]
        C_column_in_df    = df[cond_column_name]
        C_max_val         = np.amax(C_column_in_df)

        flow_column_name  = [col for col in column_names_list if DfConstants.flow_substring.lower() in col.lower()]
        flow_column_name  = flow_column_name[0]
        F_column_in_df    = df[flow_column_name]
        F_max_val         = np.amax(F_column_in_df)

        return T_column_in_df, T_max_val, C_column_in_df, C_max_val, F_column_in_df, F_max_val


    def remove_points_after_last_F_peak(self, df: pd.core.frame.DataFrame, points_after_last_F_peak_to_keep = 30, F_fraction_threshold = 40):
        '''This function removes points after last F peak since T_max (not blowout, which might not exist) to keep the relevant part only
        Then it adds points_after_last_F_peak_to_keep to the last peak and removes everything after that. Requested by Nienke
        INPUT:
            - df: dataframe we want to snip
            - points_to_keep: # of points to keep after last peak in F, remove everything after that
            - F_fraction: fraction of F above which to consider, and below which to ignore
        OUTPUT: shortened t, T, C, F series'''

        T_column_in_df, T_max_val, _, _, F_column_in_df, F_max_val = self._get_max_value_of_each_series(df)

        h_threshold    = F_max_val/F_fraction_threshold
        F_peaks_idx, _ = find_peaks(F_column_in_df, height = h_threshold)

        T_max_idx                  = np.where(T_column_in_df == T_max_val)[0][0] #added another [0] because sometimes T_max occurs at many places
        F_peaks_idx_after_T_max    = F_peaks_idx[F_peaks_idx > T_max_idx]
        first_F_peak_idx_since_Tmax= F_peaks_idx_after_T_max[0]
        last_idx_to_keep           = first_F_peak_idx_since_Tmax + points_after_last_F_peak_to_keep
        df_last_idx_to_keep        = df[:last_idx_to_keep]
        df_removed_last_pt         = df_last_idx_to_keep.reset_index(drop = True)

        return df_removed_last_pt


    @staticmethod
    def _recenter_T(T_column_in_df, T_max_val):
        '''T is not grounded to 0, ~T_min=20 and ~T_max=70.The smallest peak is 70/20=3.5x smaller than T_max, messing the analysis
        Let's bring down T by re-centering it to 0'''

        T_min_val           = np.amin(T_column_in_df)
        T_column_recentered = T_column_in_df - T_min_val
        T_max_val_recentered= T_max_val - T_min_val

        return T_column_recentered, T_max_val_recentered


    def remove_initial_points(self, df: pd.core.frame.DataFrame, points_before_first_peak_to_keep = 20, fraction_threshold = 30):
        '''This function removes points before the first peak of either T/C/F, whichever comes first to keep the relevant part only.
        Then it subtracts points_before_first_peak_to_keep from the first peak and removes everything before that. Sometimes the
        (first_peak - points_before_first_peak_to_keep) is -ve, so we set make sure that it cannot go below 0.
        After snipping the initial indices, the index is reset to 0. Function requested by Nienke
        NOTE: F series sometimes has oscillations that prevent this function from working properly,
        so F is NOT included in this function's analysis of trying to find the first peak, only T and C are
        INPUT:
            - df: dataframe we want to snip
            - points_before_first_peak_to_keep: # of points to keep before first peak, remove everything before that
        OUTPUT: shortened t, T, C, F series'''

        T_column_in_df, T_max_val, C_column_in_df, C_max_val, F_column_in_df, F_max_val = self._get_max_value_of_each_series(df)
        T_column_recentered, T_max_val_recentered = self._recenter_T(T_column_in_df, T_max_val)

        T_threshold    = T_max_val_recentered/fraction_threshold
        T_peaks_idx, _ = find_peaks(T_column_recentered, height = T_threshold)
        first_T_peak   = T_peaks_idx[0]

        C_threshold    = C_max_val/fraction_threshold
        C_peaks_idx, _ = find_peaks(C_column_in_df, height = C_threshold)
        first_C_peak   = C_peaks_idx[0]

        F_threshold    = F_max_val/fraction_threshold
        F_peaks_idx, _ = find_peaks(F_column_in_df, height = F_threshold)
        first_F_peak   = F_peaks_idx[0]

        dict_of_1st_peaks     = {'first_T_peak': first_T_peak, 'first_C_peak': first_C_peak}#, 'first_F_peak': first_F_peak}
        which_peak_is_earliest= min(dict_of_1st_peaks, key = dict_of_1st_peaks.get)
        first_peak_idx        = dict_of_1st_peaks[which_peak_is_earliest]
        first_idx_to_keep     = max(first_peak_idx - points_before_first_peak_to_keep, 0) #ensures the answer is >0

        df_removed_first_pt   = df[first_idx_to_keep:]
        df_removed_first_pt   = df_removed_first_pt.reset_index(drop = True)

        return df_removed_first_pt



class DerivativeMaker:
    '''Class that makes derivatives of data and clips these derivatives'''

    @staticmethod
    def make_derivatives(df: pd.core.frame.DataFrame, dx: int = 1) -> pd.core.frame.DataFrame:
        '''Computes 1st and 2nd derivative of dataframe
        INPUT:
              - df: input dataframe
              - dx: spacing for differentiation, default set to 1
        OUTPUT: 2 Dataframes with derived values, one for the 1st derivative, one for the 2nd derivative,
        having columns [time, temp, cond, flow]'''

        df_diff  = df.copy() # 1st derivative
        df_diff2 = df.copy() # 2nd derivative

        time_column_id       = df.columns.get_loc(DfConstants.df_time_column)
        number_of_columns    = df_diff.shape[1]
        coeff_to_offset_diff = -4 # offsets differentiation

        for i in range(time_column_id + 1, number_of_columns):
            df_diff.iloc[:, i]  = np.gradient(df.iloc[:, i], dx) # 1st derivative
            df_diff2.iloc[:, i] = np.gradient(df_diff.iloc[:, i], dx) # 2nd derivative

            # Every instance of differentiation causes an offset. Should be countered
            df_diff.iloc[:, i]  = np.roll(df_diff.iloc[:, i], coeff_to_offset_diff)
            df_diff2.iloc[:, i] = np.roll(df_diff2.iloc[:, i], coeff_to_offset_diff)

        return df_diff, df_diff2


    @staticmethod
    def clip_derivatives(df_diff: pd.core.frame.DataFrame, criterion: float = 0.005) -> pd.core.frame.DataFrame:
        '''Clipper functionality: if derivative is +ve and below X% of the max derivative value, 
        make it negative. This will make the derivative processing easier by getting rid of small bumps
        INPUT:
        - derivative dataframe
        - criterion: interpret as 'below which fraction of the max value do we neglect values?'
        OUTPUT: derivative dataframe with flipped small values'''

        dYdx = df_diff.copy()

        time_column_id = df_diff.columns.get_loc(DfConstants.df_time_column)
        num_of_columns = dYdx.shape[1]
        dY_max         = np.zeros(num_of_columns)

        for column in range(time_column_id + 1, num_of_columns):
            dY_max_val= dYdx.iloc[:, column].max()
            mask      = (dYdx.iloc[:, column] < (criterion * dY_max_val)) & (dYdx.iloc[:, column] > 0) # if derivative is +ve AND below X% of the max derivative value
            dYdx.loc[mask, dYdx.columns[column]] *= -1

        # for column in range(time_column_id + 1, num_of_columns):
        #     dY_max[column] = dYdx.iloc[:, column].max()
        #     for i, val in enumerate( dYdx.iloc[:, column] ):
        #         if (val < (criterion * dY_max[column])) & (val > 0): # if derivative is +ve AND below X% of the max derivative value
        #             dYdx.iloc[i, column] = val * -1

        return dYdx

