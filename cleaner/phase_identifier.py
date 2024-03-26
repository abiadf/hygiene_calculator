'''This module identifies the different phases of the cleaning process, namely: postmilk flush, pre-rinse, hot rinse,
and also max temperature T_max, which should occur in the hot rinse phase (hence the name). It also finds the low-C period, 
which should occur in the 'prerinse' phase. This low-C period gives us the conductivity of water without milk, so that when we have
the C of hot rinse (end goal), we can simply subtract the C of water to get the C of milk. Every feature this module looks for can be
attributed to a peak/drop in either temperature T, conductivity C, or flow F, or a combination thereof'''

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sys import exit
from scipy.signal import find_peaks

from config_info_obtainer import Constants
from logging_maker import logger
import logging

logging.getLogger('matplotlib').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)



class LowCZoneMaskHandler():
    '''Class that tries to find the low-C zone and hot rinse phase'''

    def __init__(self, var_instance):
        self.Variables = var_instance
        self.Variables.dT_relative_min_time = self.Variables.dT_relative_min_time[self.Variables.dT_relative_min_time != 0] # removes 0s (type int), which breaks loops
        self.Variables.dC_relative_min_time = self.Variables.dC_relative_min_time[self.Variables.dC_relative_min_time != 0] # removes 0s (type int), which breaks loops
        self.Variables.dF_relative_min_time = self.Variables.dF_relative_min_time[self.Variables.dF_relative_min_time != 0] # removes 0s (type int), which breaks loops

        self.Variables.dT_relative_max_time = self.Variables.dT_relative_max_time[self.Variables.dT_relative_max_time != 0] # removes 0s (type int), which breaks loops
        self.Variables.dC_relative_max_time = self.Variables.dC_relative_max_time[self.Variables.dC_relative_max_time != 0] # removes 0s (type int), which breaks loops
        self.Variables.dF_relative_max_time = self.Variables.dF_relative_max_time[self.Variables.dF_relative_max_time != 0] # removes 0s (type int), which breaks loops


    def apply_std_mask_on_dC(self, roll_window_size = 3, max_std_threshold_fraction = 0.2) -> pd.core.series.Series:
        '''Create a mask for dC values based on which values are below a certain stdev threshold
        INPUT:
            - roll_window_size: size of the rolling window to smoothen the data
            - std_threshold_fraction: fraction of the maximum std below which we want to stay
        OUTPUT: array of True/False values for when dC values are small'''

        dC_rolling_std: pd.core.series.Series = self.Variables.dC_values.rolling(roll_window_size).std().dropna() # dropna because first few samples do not fit in window, so set to NA
        dC_rolling_std_shifted = dC_rolling_std.shift(1 - roll_window_size) # to counter the shift from rolling

        max_std          = np.amax(dC_rolling_std_shifted)
        min_std          = np.amin(dC_rolling_std_shifted) # sometimes has negative value
        min_std_positive = np.abs(min_std)
        min_std_idx      = np.where(dC_rolling_std_shifted == min_std)[0]
        min_std_time     = self.Variables.t_values[min_std_idx]
        std_threshold    = max_std_threshold_fraction * max_std # we look for values with st_dev below this threshold
        dC_mask_low_std  = dC_rolling_std_shifted < std_threshold # array of True/False based on whether values respect the threshold

        # plt.plot(self.Variables.T_values)
        # plt.plot(self.Variables.C_values)
        # plt.plot(self.Variables.F_values)
        # plt.plot(self.Variables.dF_values)
        # plt.show()
        # exit()

        return dC_mask_low_std


    def apply_T_max_mask_on_dC(self, dC_mask_low_std) -> pd.core.series.Series:
        '''This function makes a mask which only considers values BEFORE T_max, because a low-C zone always occurs before T_max is achieved
        INPUT: stdev mask of dC values
        OUTPUT: mask of dC values, with values after T_max marked as False'''

        dC_mask_low_std[dC_mask_low_std.index > self.Variables.T_max_idx] = False # only consider values before T_max
        dC_mask_T_max: pd.core.series.Series = dC_mask_low_std

        return dC_mask_T_max


    def apply_C_percentile_mask_on_dC(self, dC_mask_T_max, percentile_crit = 40) -> pd.core.series.Series:
        '''This function gets C values (not dC) below a certain percentile and sets the rest to False. This mask is applied to dC (not C)
        NOTE: we are getting the index of C values and applying the indices to dC, causing array length mismatches to occur (due to differentiation)
        the function handles this
        INPUT:
            - dC_mask_T_max: T_max mask of dC values
            - percentile_crit: percentile above which we want to reject values, so if %ile=40, then 40% data is above it, so 40% of data is False
        OUTPUT: mask of dC values, with C values above a certain percentile marked as False'''

        C_percentile_value            = np.percentile(self.Variables.C_values, percentile_crit)
        C_values_above_percentile_mask= self.Variables.C_values.values > C_percentile_value # finds values > C percentile
        C_values_above_percentile_idx = np.where(C_values_above_percentile_mask)[0]

        array_mismatch_len_due_to_diff= len(C_values_above_percentile_mask) - len(dC_mask_T_max) # array mismatch between C and dC due to differentiation
        adjusted_False_indices        = C_values_above_percentile_idx - array_mismatch_len_due_to_diff # subtracts the indices of first few values (useless due to differentiation)
        adjusted_False_indices        = adjusted_False_indices[adjusted_False_indices >= array_mismatch_len_due_to_diff] # removes the first items
        dC_mask_T_max[adjusted_False_indices] = False
 
        dC_mask_C_percentile: pd.core.series.Series = dC_mask_T_max
        return dC_mask_C_percentile



class EarlyCmaxHandler(LowCZoneMaskHandler):
    '''Class that tries to find the early C-max, a feature that affects some files. This is characterized by a very large peak in C
    in the initial phases. This class aims to find it and remove its'''

    def __init__(self, var_instance):
        super().__init__(var_instance)


    # maybe good idea to do additional check: if 1st peak is higher than 2nd peak then we have an early C_max
    def detect_if_early_C_max_exists(self, large_C_search_time_fraction_threshold = 0.25):
        '''Sometimes we get a very sharp early peak in C, earlier than postmilk flush, which messes our analysis. The data is already
        pre-processed and smoothened before looking for phases; however, this is not enough to get rid of large peaks in C.
        Let's use a time criterion to filter out C values. This function ignores C_max if it is in the earliest X% time
        INPUT:
            - large_C_search_time_fraction_threshold: time fraction before which we ignore large C peaks
        OUTPUT: is_there_early_large_C: tells if we detected an early large C, 0=No 1=Yes'''

        PERCENT = 100
        is_there_early_large_C: int= 0
        number_of_items_in_series  = len(self.Variables.df_indices.values)
        large_C_threshold_time_idx = int(number_of_items_in_series * large_C_search_time_fraction_threshold)
        
        try:
            large_C_threshold_time = np.where(self.Variables.t_values == large_C_threshold_time_idx)
        except:
            large_C_threshold_time = np.argmin(np.abs(self.Variables.t_values - large_C_threshold_time)) #estimates nearest index to our time
        finally:
            time_fraction_int      = int(large_C_search_time_fraction_threshold * PERCENT)
            large_C_threshold_time = self.Variables.t_values[time_fraction_int]

        if self.Variables.C_max_idx < large_C_threshold_time_idx:
            logger.warning(f"C max (idx {self.Variables.C_max_idx}) is within {large_C_search_time_fraction_threshold*PERCENT}% of time (idx {large_C_threshold_time_idx})")
            is_there_early_large_C = 1
        else:
            logger.info(f"C max (idx {self.Variables.C_max_idx}) is outside {large_C_search_time_fraction_threshold*PERCENT}% of time (idx {large_C_threshold_time_idx})")
        
        # dC_peaks_values  = self.Variables.dC_values[self.Variables.dC_rel_max_idx.values]
        # sorted_dC_array  = np.sort(dC_peaks_values)
        # first_largest_dC = sorted_dC_array[-1]
        # second_largest_dC= sorted_dC_array[-2]
        # crit_between_peaks = 1/C_max_threshold_fraction
    
        return is_there_early_large_C


    def _find_indices_of_start_and_end_of_large_C_peak(self):
        '''This function starts from C_max peak, and goes down to find the first point below C_mean. It does that for each side, left and right
        We get 2 indices, one from each side of C_max, which frame the 'early large C' feature
        OUTPUT:
            - first_idx_below_mean_right: first index that is below mean when going from C_max downward to the RIGHT
            - first_idx_below_mean_left: first index that is below mean when going from C_max downward to the LEFT'''

        first_C_max_idx_below_mean_right = self.Variables.C_max_idx + np.argmax(self.Variables.C_values[self.Variables.C_max_idx:] <= self.Variables.C_mean) # start from C_max and walk forward
        first_C_max_idx_below_mean_left  = self.Variables.C_max_idx - np.argmax(self.Variables.C_values[self.Variables.C_max_idx::-1] <= self.Variables.C_mean) # start from C_max and walk backward

        logger.info(f"Early C_max starts at idx {first_C_max_idx_below_mean_left} and ends at idx {first_C_max_idx_below_mean_right}")
        return first_C_max_idx_below_mean_right, first_C_max_idx_below_mean_left


    def smoothen_large_C_peak_values_if_it_exists(self, is_there_early_large_C):
        '''This function reduces the zone of early C peak by first squashing C and dC then smoothening both
        INPUT: is_there_early_large_C: whether there is an early large C peak (0=False, 1=True)
        No output as this writes to self'''

        if is_there_early_large_C:
            first_C_max_idx_below_mean_right, first_C_max_idx_below_mean_left = self._find_indices_of_start_and_end_of_large_C_peak()

            C_large_peak_copy  = self.Variables.C_values[first_C_max_idx_below_mean_left : first_C_max_idx_below_mean_right + 1].copy()
            C_large_peak_copy  = C_large_peak_copy.astype('float64')
            reduction_factor   = self.Variables.C_mean/self.Variables.C_max
            C_large_peak_copy *= reduction_factor
            smoothed_part      = C_large_peak_copy.rolling(window = 2).mean()
            smoothed_part.fillna(C_large_peak_copy, inplace = True) # fill gaps between C_max zone and part before it
            self.Variables.C_values.values[first_C_max_idx_below_mean_left : first_C_max_idx_below_mean_right + 1] = smoothed_part.values

            dC_mean            = self.Variables.dC_values.mean()
            reduction_factor2  = dC_mean/self.Variables.dC_max_val
            self.Variables.dC_values.values[first_C_max_idx_below_mean_left : first_C_max_idx_below_mean_right + 1] *= reduction_factor2
        
            logger.info(f"Just smoothened C and dC by {reduction_factor} and {reduction_factor2} times respectively")
        else:
            logger.info(f"Did NOT smoothen C and dC")



class LowCZoneAndHotrinseFinder(LowCZoneMaskHandler):
    '''Class that finds the low-C zone and the hot rinse phase. The low-C zone is marked by a long stretch of very low C and T, denoting 
    that there is only water in the system. It usually occurs during the pre-rinse phase'''

    SECS_PER_MINUTE = 60
    
    def __init__(self, var_instance):
        super().__init__(var_instance)


    def group_low_C_zones(self, dC_mask_C_percentile: pd.core.series.Series):
        '''We have a pd series of True/False values. This function groups them into a list of True zones (True = low-C)
        NOTE: this function's input is a mask applied to dC, where the condition is 'is this value higher than the %ile of C values?'
        INPUT: dC_mask_C_percentile: pre-existing mask of True/False values applied to dC
        OUTPUT: low_C_zones: list of tuples shaped like: [(start_idx_1, duration_1), (start_idx_2, duration_2), ...] '''

        low_C_zones_list: list = []
        current_start_index    = None

        for idx, value in dC_mask_C_percentile.items():
            if value and (current_start_index is None):
                current_start_index = idx
            elif (not value) and (current_start_index is not None):
                duration = idx - current_start_index
                low_C_zones_list.append((current_start_index, duration))
                # low_C_zones_list.append({'start_idx': current_start_index, 'duration': idx - current_start_index})
                current_start_index = None
        if (current_start_index is not None):
            duration = len(dC_mask_C_percentile) - current_start_index
            low_C_zones_list.append((current_start_index, duration))
            # low_C_zones_list.append({'start_idx': current_start_index, 'duration': len(dC_mask_C_percentile) - current_start_index})

        logger.info(f"Found {len(low_C_zones_list)} low-C zones")
        return low_C_zones_list


    def obtain_best_low_C_zone_candidate(self, low_C_zones: list, duration_threshold: int = 120, decreases_by: int = -10):
        '''We have a list of low-C zones, with their start index and duration. This function aims to find the real low-C zone by:
        spotting the first zone that exceeds a certain duration criterion. If no zone exceeds the duration criterion, we lower it and try again
        INPUT:
            - duration_threshold: duration threshold which tells us we have a low-C zone
            - decreases_by: how much to decrease the duration_threshold at every loop if we cannot find a low-C zone candidate
            - low_C_zones: list of tuples shaped like: [(start_idx_1, duration_1), (start_idx_2, duration_2), ...]
        OUTPUT: low_C_zone_start_time, low_C_zone_start_idx, zone_duration_s'''

        list_of_duration_thresholds: list = list(range(duration_threshold, 0, decreases_by))

        for duration_crit in list_of_duration_thresholds:
            for zone in low_C_zones:
                zone_duration_s = zone[1]
                if zone_duration_s >= duration_crit:
                    low_C_zone_start_idx = zone[0]
                    low_C_zone_start_time= self.Variables.t_values[low_C_zone_start_idx]
                    logger.info(f"Low-C zone lasts {zone_duration_s}s, starts @ {low_C_zone_start_time}, idx {low_C_zone_start_idx}")
                    
                    return low_C_zone_start_time, low_C_zone_start_idx, zone_duration_s

        logger.warning(f"Cannot find zone that meets duration threshold, using longest one instead")

        zone_with_longest_duration= max(low_C_zones, key = lambda x: x[1])
        low_C_zone_start_idx      = zone_with_longest_duration[0]
        low_C_zone_start_time     = self.Variables.t_values[low_C_zone_start_idx]
        zone_duration_s           = zone_with_longest_duration[1]
        logger.info(f"Low C lasts {zone_duration_s}s, starts @ {low_C_zone_start_time}, idx {low_C_zone_start_idx}")
        return low_C_zone_start_time, low_C_zone_start_idx, zone_duration_s


    def get_low_C_zone_KPIs(self, low_C_zone_start_time, low_C_zone_start_idx, zone_duration_s):
        '''Look for end of low-C period. Use dC to spot the period of stillness. NOTE: low-C period consists of WATER ONLY
        Pre-rinse must occur before C_max (which happens during hot rinse)
        INPUT: 
            - low_C_zone_start_time: start time of low-C zone
            - low_C_zone_start_idx: start index of low-C zone
            - zone_duration_s: duration of low-C zone in s
        OUTPUT: low_C_zone_KPIs'''

        '''Don't forget to add the offset time'''
        low_C_zone_end_idx  = low_C_zone_start_idx + zone_duration_s
        zone_duration_td    = zone_duration_s * pd.Timedelta(seconds = 1)
        low_C_zone_end_time = low_C_zone_start_time + zone_duration_td
        low_C_zone_values   = self.Variables.C_values[low_C_zone_start_idx : low_C_zone_end_idx + 1].values # this is water

        if low_C_zone_values.size > 0:
            C_recession_std = np.std(low_C_zone_values)
            C_recession_avg = np.mean(low_C_zone_values)
        else:
            C_recession_std = 0
            C_recession_avg = 0
            logger.warning("The C list is empty")

        low_C_zone_min  = np.min(low_C_zone_values, initial=0)
        low_C_zone_max  = np.max(low_C_zone_values, initial=0)

        low_C_zone_KPIs = {# 'longest recession idx':            max_recession_idx,
                           'low-C zone start time [s]': low_C_zone_start_time,
                           'low-C zone end time [s]':   low_C_zone_end_time,
                           'low-C zone start idx [#]':  low_C_zone_start_idx,
                           'low-C zone end idx [#]':    low_C_zone_end_idx,
                           'low-C zone duration [s]':   zone_duration_s,
                           'C avg (water)':             C_recession_avg,
                           'C min (water)':             low_C_zone_min,
                           'C max (water)':             low_C_zone_max,
                           'C std (water)':             C_recession_std, }

        logger.info(f"Low-C zone @ [{low_C_zone_start_time}-{low_C_zone_end_time}], idx #[{low_C_zone_start_idx}-{low_C_zone_end_idx}]")
        return low_C_zone_KPIs


    def find_hot_rinse_time(self, low_C_zone_KPIs, num_neighbors = 8, time_between_hotrinse_Tmax_in_min = 4):
        '''Hot_rinse = peak in T AND C.
        In the for loop, we make sure that time is after low-C zone ends and before T_max occurs, because hot rinse happens before that
        INPUT:
            - low_C_zone_KPIs: dict that gives us the end of C period
            - num_neighbors: # of seconds before and after peak in T to look for peak in C. Say T_peak @ 10:20 and we have num_neighbors = 10,
              then we look for C_peak in the range [10:10; 10:30] 
            - time_between_hotrinse_Tmax_in_min: fallback value if we cannot find hot rinse. Default is based on data which shows
              that hot rinse occurs about 4 min before T_max
        OUTPUT:
            - hotrinse_time: time at which hot rinse occurs
            - hotrinse_idx: index at which hot rinse occurs'''

        T_crit_fraction = 0.3
        T_threshold     = self.Variables.T_values.values.mean() * T_crit_fraction # ignore values <T_threshold (ie small peaks)

        C_crit_fraction = 0.5
        C_threshold     = self.Variables.C_values.values.mean() * C_crit_fraction # ignore values <C_threshold (ie small peaks)

        neighbors_duration = num_neighbors * pd.Timedelta(seconds = 1)

        for time in self.Variables.dT_relative_max_time:
            if (low_C_zone_KPIs['low-C zone end time [s]'] < time < self.Variables.T_max_time):
                idx = np.where(self.Variables.t_values == time)[0][0] 
                if self.Variables.T_values[idx] > T_threshold: # ignore small T peaks
                    neighbors_start = time - neighbors_duration
                    neighbors_end   = time + neighbors_duration

                    for time2 in self.Variables.dC_relative_max_time:
                        if isinstance(time2, pd.Timestamp): # safeguard that loop doesnt break when time_value = 0 (type int) by enforcing type 'pd.Timestamp'
                            idx2 = np.where(self.Variables.t_values == time2)[0][0]
                            if self.Variables.C_values[idx2] > C_threshold: # ignore small C peaks
                                if (low_C_zone_KPIs['low-C zone end time [s]'] < time2 < self.Variables.T_max_time):
                                    if neighbors_start < time2 < neighbors_end:
                                        hotrinse_time = time2
                                        hotrinse_idx  = np.where(self.Variables.t_values == hotrinse_time)[0][0]
                                        logger.info(f"Hot rinse @ {hotrinse_time}, idx #{hotrinse_idx}")
                                        return hotrinse_time, hotrinse_idx

        time_before_Tmax_in_s = self.SECS_PER_MINUTE * time_between_hotrinse_Tmax_in_min
        time_buffer_td        = pd.Timedelta(time_before_Tmax_in_s, unit = 's')
        hotrinse_time         = self.Variables.T_max_time - time_buffer_td
        hotrinse_idx          = np.argmin(np.abs(self.Variables.t_values - hotrinse_time)) # estimates nearest index to our time
        logger.warning(f"Could not find hot-rinse, setting it {time_between_hotrinse_Tmax_in_min}min before Tmax")
        logger.info(f"Hot rinse @ {hotrinse_time}, idx #{hotrinse_idx}")
        return hotrinse_time, hotrinse_idx



class PrerinsePostmilkflushFinder(LowCZoneMaskHandler):
    '''Class that finds the pre-rinse, then the postmilk flush phases'''

    SECS_PER_MINUTE = 60
    
    def __init__(self, var_instance):
        super().__init__(var_instance)


    def _set_default_prerinse_time_if_far_from_hotrinse(self, hotrinse_idx, prerinse_hotrinse_limit_s):
        '''This funciton implements the prerinse-hotrinse limit set by Nienke of 200s'''

        prerinse_idx  = hotrinse_idx - prerinse_hotrinse_limit_s
        prerinse_time = self.Variables.t_values[prerinse_idx]
        logger.warning(f"Exceeded the prerinse-hotrinse limit of {prerinse_hotrinse_limit_s}s! Defaulting prerinse @ {prerinse_time}, idx #{prerinse_idx}")
        return prerinse_time, prerinse_idx


    def find_prerinse_time(self, low_C_zone_start_time, hotrinse_idx, time_between_prerinse_Tmax_in_min = 7, prerinse_hotrinse_limit_s = 200):
        '''Pre-rinse = 1st large peak in F, AND drop in C, before low-C zone. The code checks if dF_peaks and dC_drops are empty before low-C zone.
        If one of them is empty, then code takes the last peak/drop in the other as prerinse time. If both are non-empty, it takes the
        last dC drop before low-C zone. If both are empty, it assumes the low-C zone is wrongly made and sets prerinse to the default value
        NOTE: in this function we often take the last value like [-1], because it is the one closest to low-C
        INPUT:
            - num_neighbors: # of seconds before and after peak in F to look for DROP in C. Say F_peak @ 10:20 and we have num_neighbors = 10,
              then we look for C_drop in range [10:10; 10:30] 
            - time_between_prerinse_Tmax_in_min: fallback value if we cannot find prerinse. Data shows that prerinse occurs 
              about 10 before Tmax, so it is defaulted to 2 min
        OUTPUT: 
            - prerinse_time: time at which pre-rinse occurs
            - prerinse_idx: index at which pre-rinse occurs'''

        dF_peaks_before_low_C = self.Variables.dF_relative_max_time[self.Variables.dF_relative_max_time <= low_C_zone_start_time]
        dC_drops_before_low_C = self.Variables.dC_relative_min_time[self.Variables.dC_relative_min_time <= low_C_zone_start_time]

        if (dF_peaks_before_low_C.empty) and (dC_drops_before_low_C.empty):
            logger.warning(f"Both dC drops and dF peaks before low-C zone are empty, low-C zone is probably wrong")
            logger.info(f"Setting dC drops and dF peaks to default values of {time_between_prerinse_Tmax_in_min} min before T_max")
            time_before_Tmax_in_s = self.SECS_PER_MINUTE * time_between_prerinse_Tmax_in_min
            time_buffer_td        = pd.Timedelta(time_before_Tmax_in_s, unit = 's')
            prerinse_time         = self.Variables.T_max_time - time_buffer_td
            prerinse_idx          = np.argmin(np.abs(self.Variables.t_values - prerinse_time)) #estimates nearest index to our time
            logger.warning(f"Could not find pre-rinse, setting it {time_between_prerinse_Tmax_in_min} min before T_max")
            logger.info(f"Pre rinse @ {prerinse_time}, idx #{prerinse_idx}")
            
            prerinse_time_pd = pd.to_datetime(prerinse_time)
            prerinse_time    = prerinse_time_pd.strftime('%H:%M:%S')
            return prerinse_time, prerinse_idx
        else:
            if dF_peaks_before_low_C.empty:
                logger.warning(f"There are no dF peaks before low_C_zone_start_time")
                prerinse_time = dC_drops_before_low_C.values[-1]
            elif dC_drops_before_low_C.empty:
                logger.warning(f"There are no dC drops before low_C_zone_start_time")
                prerinse_time = dF_peaks_before_low_C.values[-1]
            else:
                prerinse_time = dC_drops_before_low_C.values[-1]

        prerinse_idx    = np.where(self.Variables.t_values == prerinse_time)[0][0]
        prerinse_time_pd= pd.to_datetime(prerinse_time)
        prerinse_time   = prerinse_time_pd.strftime('%H:%M:%S')
        logger.info(f"Pre rinse @ {prerinse_time}, idx #{prerinse_idx}")

        if (hotrinse_idx - prerinse_idx) > prerinse_hotrinse_limit_s:
            prerinse_time, prerinse_idx = self._set_default_prerinse_time_if_far_from_hotrinse(hotrinse_idx, prerinse_hotrinse_limit_s)
            prerinse_time = prerinse_time.strftime('%H:%M:%S')

        return prerinse_time, prerinse_idx


    # # remove this function when the alternate prerinse finder works
    # def find_prerinse_time(self, post_milk_flush_time, post_milk_flush_idx, num_neighbors = 8, F_crit_fraction = 0.5, time_between_postmilk_prerinse_in_min = 2):
    #     '''pre-rinse = 1st large peak in F, AND drop in C
    #     In the loop, we make sure time is less than the time T_max occurs, simply because pre-rinse happens before that
    #     INPUT:
    #         - post_milk_flush_time
    #         - post_milk_flush_idx
    #         - num_neighbors: # of seconds before and after peak in F to look for DROP in C. Say F_peak @ 10:20 and we have num_neighbors = 10,
    #           then we look for C_drop in range [10:10; 10:30] 
    #         - F_crit_fraction: fraction of F used to filter F-values
    #         - time_between_postmilk_prerinse_in_min: fallback value if we cannot find prerinse. Data shows that prerinse occurs 
    #           about 2 min after postmilk, so it is defaulted to 2 min
    #     OUTPUT: 
    #         - prerinse_time: time at which pre-rinse occurs
    #         - prerinse_idx: index at which pre-rinse occurs'''

    #     F_threshold         = self.Variables.F_values.values.mean() * F_crit_fraction # ignore anything below F_threshold (ie small peaks)
    #     neighbors_duration  = num_neighbors * pd.Timedelta(seconds = 1)

    #     for time in (self.Variables.dF_relative_max_time):
    #         if (post_milk_flush_time < time < self.Variables.T_max_time):
    #             F_idx = np.where(self.Variables.t_values == time)[0][0] 
    #             if self.Variables.F_values[F_idx] > F_threshold: # ignore small F peaks
    #                 neighbors_start    = time - neighbors_duration
    #                 neighbors_end      = time + neighbors_duration

    #                 for time_value in self.Variables.dC_relative_min_time:
    #                     if (post_milk_flush_time < time_value < self.Variables.T_max_time):
    #                         if neighbors_start < time_value < neighbors_end:
    #                             prerinse_time = time_value
    #                             prerinse_idx  = np.where(self.Variables.t_values == prerinse_time)[0][0]
    #                             logger.info(f"Pre rinse @ {prerinse_time}, idx #{prerinse_idx}")
    #                             return prerinse_time, prerinse_idx

    #     time_after_postmilk_in_s= self.SECS_PER_MINUTE * time_between_postmilk_prerinse_in_min
    #     time_buffer_td          = pd.Timedelta(time_after_postmilk_in_s, unit = 's')
    #     prerinse_time           = post_milk_flush_time + time_buffer_td
    #     prerinse_idx            = np.argmin(np.abs(self.Variables.t_values - prerinse_time)) #estimates nearest index to our time
    #     logger.warning(f"Could not find pre-rinse, setting it {time_between_postmilk_prerinse_in_min} min after postmilk flush")
    #     logger.info(f"Pre rinse @ {prerinse_time}, idx #{prerinse_idx}")
    #     return prerinse_time, prerinse_idx


    def _find_postmilk_time_when_no_early_sharp_C(self, low_C_zone_start_time, hotrinse_idx, time_between_postmilk_Tmax_in_min: int = 12, C_crit_fraction = 0.1):
        '''Post-milk = 1st positive peak in C. If this method fails to find the post-milk flush, we fallback onto a hardcoded
        time value of postmilk flush, measured from T_max.
        INPUT: 
            - time_between_postmilk_Tmax_in_min: fallback value if we cannot get a postmilkflush value. Default is based on data which shows
              that postmilk occurs about 12 min before T_max
            - C_crit_fraction: threshold fraction below which we ignore everything
            OUTPUT:
            - post_milk_flush_time: time at which postmilk flush occurs
            - post_milk_flush_idx: index at which postmilk flush occurs'''

        _, prerinse_idx = self.find_prerinse_time(low_C_zone_start_time, hotrinse_idx)

        C_threshold = self.Variables.C_values.values.mean() * C_crit_fraction # ignore anything below C_threshold (ie small peaks)

        for post_milk_flush_time in self.Variables.dC_relative_max_time:
            post_milk_flush_idx = np.where(self.Variables.t_values == post_milk_flush_time)[0][0]
            if post_milk_flush_idx < prerinse_idx:
                if self.Variables.C_values[post_milk_flush_idx] > C_threshold:
                    logger.info(f"Post-milk flush @ {post_milk_flush_time}, idx #{post_milk_flush_idx}")
                    return post_milk_flush_time, post_milk_flush_idx
        
        time_before_T_max_in_s= self.SECS_PER_MINUTE * time_between_postmilk_Tmax_in_min
        time_buffer_td        = pd.Timedelta(time_before_T_max_in_s, unit = 's')
        post_milk_flush_time  = self.Variables.T_max_time - time_buffer_td
        post_milk_flush_idx   = np.argmin(np.abs(self.Variables.t_values - post_milk_flush_time)) #estimates nearest index to our time
        
        logger.warning(f"Could not find post-milk flush, using the default value, {time_between_postmilk_Tmax_in_min} min before T_max")
        logger.info(f"Post-milk flush @ {post_milk_flush_time}, idx #{post_milk_flush_idx}")
        return post_milk_flush_time, post_milk_flush_idx


    # consider having an additional function that finds postmilk using C and T, if C and F doesnt work well
    def _find_postmilk_time_when_early_sharp_C(self, low_C_zone_start_time, num_neighbors = 8, time_between_postmilk_Tmax_in_min: int = 12, C_crit_fraction = 0.01):
        '''If there is early C peak, then C is not reliable to determine postmilk flush on its own, so this function looks for increase in C AND F
        In the event of failure, we fall back to a default time value of postmilk flush, measured from T_max.
        INPUT:
            - time_between_postmilk_Tmax_in_min: fallback value if we cannot get a postmilkflush value. Default is based on data which shows
              that postmilk occurs about 12 min before T_max
        OUTPUT:
            - post_milk_flush_time: time at which postmilk flush occurs
            - post_milk_flush_idx: index at which postmilk flush occurs'''

        neighbors_duration= num_neighbors * pd.Timedelta(seconds = 1)
        C_threshold       = self.Variables.C_values.values.mean() * C_crit_fraction # ignore anything below C_threshold (ie small peaks

        F_crit_fraction= C_crit_fraction
        F_threshold    = self.Variables.C_values.values.mean() * F_crit_fraction # ignore anything below C_threshold (ie small peaks

        for time in (self.Variables.dC_relative_max_time):
            if (time < low_C_zone_start_time):
                C_idx = np.where(self.Variables.t_values == time)[0][0] 
                if self.Variables.C_values[C_idx] > C_threshold: # ignore small C peaks
                    neighbors_start = time - neighbors_duration
                    neighbors_end   = time + neighbors_duration

                    for time_value in self.Variables.dF_relative_max_time:
                        if (time_value < low_C_zone_start_time):
                            F_idx = np.where(self.Variables.t_values == time)[0][0] 
                            if self.Variables.F_values[F_idx] > F_threshold: # ignore small C peaks
                                if neighbors_start < time_value < neighbors_end:
                                    postmilkflush_time = time_value
                                    postmilkflush_idx  = np.where(self.Variables.t_values == postmilkflush_time)[0][0]
                                    logger.info(f"Pre rinse @ {postmilkflush_time}, idx #{postmilkflush_idx}")
                                    return postmilkflush_time, postmilkflush_idx

        time_before_T_max_in_s= self.SECS_PER_MINUTE * time_between_postmilk_Tmax_in_min
        time_buffer_td        = pd.Timedelta(time_before_T_max_in_s, unit = 's')
        post_milk_flush_time  = self.Variables.T_max_time - time_buffer_td
        post_milk_flush_idx   = np.argmin(np.abs(self.Variables.t_values - post_milk_flush_time)) #estimates nearest index to our time
        
        logger.warning(f"Could not find post-milk flush, using the default value, {time_between_postmilk_Tmax_in_min} min before T_max")
        logger.info(f"Post-milk flush @ {post_milk_flush_time}, idx #{post_milk_flush_idx}")
        return post_milk_flush_time, post_milk_flush_idx


    def find_postmilk_flush_time_depending_on_early_sharp_C(self, is_there_early_large_C, low_C_zone_start_time, hotrinse_idx):
        '''Run the helper functions. If there is an early large C, then run the function for it. If there isn't a large early C, then run
        the normal function to detect postmilk flush
        INPUT:
            - is_there_early_large_C: True/False value indicating whether there is an early large C
            - low_C_zone_start_time: start time of the low-C zone
        OUTPUT:
            - post_milk_flush_time: start time of postmilk flush
            - post_milk_flush_idx: start idx of postmilk flush'''

        if is_there_early_large_C:
            post_milk_flush_time, post_milk_flush_idx = self._find_postmilk_time_when_early_sharp_C(low_C_zone_start_time, num_neighbors = 8, time_between_postmilk_Tmax_in_min = 12, C_crit_fraction = 0.01)
        else:
            post_milk_flush_time, post_milk_flush_idx = self._find_postmilk_time_when_no_early_sharp_C(low_C_zone_start_time, hotrinse_idx, time_between_postmilk_Tmax_in_min = 12, C_crit_fraction = 0.01)

        return post_milk_flush_time, post_milk_flush_idx



class PostRinseFinder(LowCZoneMaskHandler):
    '''Class dealing with postrinse phase, inherits from LowCZoneMaskHandler'''

    def __init__(self, var_instance):
        super().__init__(var_instance)


    def find_post_rinse_start_time(self, num_neighbors = 8, Tmax_postrinse_timeout_s = 60):
        '''Post-rinse = 1st drop in T AND C since T_max
        We allow C_drop to occur before T_max, but T_drop cannot (because every T point after T_max is mathematically a 'drop')
        First, we look for drops in T after T_max, then we see if these have a nearby drop in C. If so, then postrinse is set to
        whichever of these (t_T or t_C) is larger. This helps find the end of postrinse.
        If we cannot find post-rinse, then make it start at T_max.
        If postrinse starts at >1min after Tmax, then we take the first T drop after Tmax
        INPUT:
            - num_neighbors: # of seconds before OR after drop in T to look for drop in C. Say T_peak @ 10:20 and num_neighbors = 10,
              then we look for C_peak in [10:10; 10:30]. Not recommended to go below 6s
            - Tmax_postrinse_timeout: time between Tmax and postrinse that cannot be exceeded
        OUTPUT:
            - postrinse_time: time at which postrinse occurs
            - postrinse_idx: index at which postrinse occurs'''

        logger.info(f"T_max @ {self.Variables.T_max_time}")
        neighbors_duration = num_neighbors * pd.Timedelta(seconds = 1)

        for time in self.Variables.dT_relative_min_time:
            if time > self.Variables.T_max_time:
                neighbors_start = time - neighbors_duration
                neighbors_end   = time + neighbors_duration

                for time_value in self.Variables.dC_relative_min_time:
                    if neighbors_start < time_value < neighbors_end:
                        postrinse_time = max(time, time_value)
                        time_diff_in_s = (postrinse_time - self.Variables.T_max_time).total_seconds()
                        if time_diff_in_s > Tmax_postrinse_timeout_s:
                            logger.warning(f"Postrinse takes too long to occur (>{Tmax_postrinse_timeout_s}s since T_max), will take the 1st peak in T since T_max instead")
                            postrinse_time_list = [x for x in self.Variables.dT_relative_min_time if x > self.Variables.T_max_time]
                            postrinse_time2 = postrinse_time_list[0] #take 1st value of list of peak
                            postrinse_idx2  = np.where(self.Variables.t_values == postrinse_time2)[0][0]
                            logger.info(f"Post rinse starts @ {postrinse_time2}, idx #{postrinse_idx2}")
                            return postrinse_time2, postrinse_idx2
                        else:
                            postrinse_idx = np.where(self.Variables.t_values == postrinse_time)[0][0]
                            logger.info(f"Post rinse starts @ {postrinse_time}, idx #{postrinse_idx}")
                            return postrinse_time, postrinse_idx

        logger.warning(f"Could not find post-rinse start, setting it to T_max")
        logger.info(f"Post rinse @ {self.Variables.T_max_time}, idx #{self.Variables.T_max_idx}")
        return self.Variables.T_max_time, self.Variables.T_max_idx


    def _find_postrinse_end_using_T(self, num_neighbors, dT_max_after_postrinse_series, dC_max_after_postrinse_series):
        '''Helper function that finds end of postrinse using the T variable. First, gets time of first dT peak after postrinse start,
        then applies a range of neighbors to this dT value to see if dC peaks match with it. If neighbors match,
        then we found postrinse end time. If not, then just return first dT peak'''

        if len(dT_max_after_postrinse_series) > 0: # dT array sometimes empty, so ensure it has values by len() > 0

            first_peak_after_postrinse_time = dT_max_after_postrinse_series.iloc[0]
            neighbors_duration= num_neighbors * pd.Timedelta(seconds = 1)
            neighbors_start   = first_peak_after_postrinse_time - neighbors_duration
            neighbors_end     = first_peak_after_postrinse_time + neighbors_duration

            for time in dC_max_after_postrinse_series: #using dC here as neighbors are defined by T
                if neighbors_start < time < neighbors_end:
                    postrinse_end_time = time
                    postrinse_end_idx  = np.where(self.Variables.t_values == postrinse_end_time)[0][0]
                    logger.info(f"Post rinse ends @ {postrinse_end_time}, idx #{postrinse_end_idx}, using T method")
                    return postrinse_end_time, postrinse_end_idx

            postrinse_end_idx = np.where(self.Variables.t_values == first_peak_after_postrinse_time)[0][0]
            logger.warning(f"Could not find end of postrinse, setting it to 1st peak in T since T_max")
            logger.info(f"Post rinse ends @ {first_peak_after_postrinse_time}, idx #{postrinse_end_idx}, using T method")
            return first_peak_after_postrinse_time, postrinse_end_idx
        else:
            logger.warning("Array of dT peaks after postrinse start is of size 0")
            return None


    def _find_postrinse_end_using_C(self, dC_max_after_postrinse_series):
        '''Helper function that finds end of postrinse using the C variable. This is used when methods using T fail.
        Finds the first peak in dC since postrinse start and sets it as postrinse end time'''

        if len(dC_max_after_postrinse_series) > 0:
            logger.info(f"Using C method instead, less stable, so results might be less accurate")
            postrinse_end_time = dC_max_after_postrinse_series.iloc[0] # take first value
            postrinse_end_idx  = np.where(self.Variables.t_values == postrinse_end_time)[0][0]
            logger.info(f"Post rinse ends @ {postrinse_end_time}, idx #{postrinse_end_idx}, using C method")
            return postrinse_end_time, postrinse_end_idx
        else:
            logger.warning("Array of dC peaks after postrinse start is of size 0")
            return None

    
    def _find_postrinse_end_using_backup(self, postrinse_time, postrinse_default_duration_s = 60):
        '''Helper function to be used when both T and C cannot be used. This function uses default values
        to get the postrinse end time'''

        logger.warning(f"Cannot find peaks in either T or C after T_max, using the criterion of {postrinse_default_duration_s}s")
        time_buffer_td     = pd.Timedelta(postrinse_default_duration_s, unit = 's')
        postrinse_end_time = postrinse_time + time_buffer_td
        postrinse_end_idx  = np.argmin(np.abs(self.Variables.t_values - postrinse_end_time)) #estimates nearest index to our time
        logger.warning(f"Could not find postrinse end, setting it {postrinse_default_duration_s}s after postrinse start")
        logger.info(f"Postrinse @ {postrinse_end_time}, idx #{postrinse_end_idx}")
        return postrinse_end_time, postrinse_end_idx


    def find_post_rinse_end_time(self, postrinse_time, num_neighbors = 8, postrinse_duration_limit_s = 90):
        '''Post-rinse ends when T and C start to increase. So will detect it when dC and dT each has a maximum that occurs after postrinse.
        First, find when T begins to increase (= dT_max) after postrinse, then see if it is close to another dC_max, up to #_neighbors.
        dC fluctuates more than dT, so will mainly work with dT, then compare with dC. If we find a dC value within neighbors range, we take
        the time of this dC value
        If dT_rel_max values has no peaks after postrinse, then try with dC_rel_max. If not working, then use default value
        INPUT:
            - postrinse_time
            - num_neighbors
            - postrinse_duration_s: default duration of postrinse period in case everything fails. Default to 1.5 min
        OUTPUT: '''

        dT_max_after_postrinse_series = self.Variables.dT_relative_max_time[self.Variables.dT_relative_max_time > postrinse_time]
        dC_max_after_postrinse_series = self.Variables.dC_relative_max_time[self.Variables.dC_relative_max_time > postrinse_time]

        postrinse_results_from_T_method = self._find_postrinse_end_using_T(num_neighbors, dT_max_after_postrinse_series, dC_max_after_postrinse_series)
        if postrinse_results_from_T_method is not None:
            postrinse_end_time, _ = postrinse_results_from_T_method
            postrinse_duration_s  = (postrinse_end_time - postrinse_time).total_seconds()
            if postrinse_duration_s < postrinse_duration_limit_s:
                logger.info(f"Postrinse lasts {postrinse_duration_s}s, less than {postrinse_duration_limit_s}s (default)")
                return postrinse_results_from_T_method
            else:
                logger.warning(f"Postrinse lasts more than {postrinse_duration_limit_s}s, will try C method")

        postrinse_results_from_C_method = self._find_postrinse_end_using_C(dC_max_after_postrinse_series)
        if postrinse_results_from_C_method is not None:
            postrinse_end_time, _ = postrinse_results_from_C_method
            postrinse_duration_s  = (postrinse_end_time - postrinse_time).total_seconds()
            if postrinse_duration_s < postrinse_duration_limit_s:
                logger.info(f"Postrinse lasts {postrinse_duration_s}s, less than {postrinse_duration_limit_s}s (default)")
                return postrinse_results_from_C_method
            else:
                logger.warning(f"Postrinse lasts more than {postrinse_duration_limit_s}s, will use default value instead")

        logger.warning("Using default values")
        return self._find_postrinse_end_using_backup(postrinse_time, 60)


    def collect_rinse_KPIs(self, hot_rinse_idx, post_rinse_idx, low_C_zone_KPIs, solution_type):
        '''This function gets the C of the hot rinse'''
        
        C_mean_hot_rinse = self.Variables.C_values[hot_rinse_idx: post_rinse_idx].mean()
        logger.info(f"C_hotrinse = {C_mean_hot_rinse}")

        C_water = low_C_zone_KPIs['C avg (water)']
        C_mean_hot_rinse_no_water = C_mean_hot_rinse - C_water
        logger.info(f"C_hotrinse (no water) = {C_mean_hot_rinse_no_water} mS/cm")

        logger.info(f"Reminder: the solution is {solution_type.upper()}")

        if solution_type == Constants.acid_keyword:
            C_mean_hot_rinse_no_water_percent = C_mean_hot_rinse_no_water/Constants.sigma_acid
        elif solution_type == Constants.alkaline_keyword:
            C_mean_hot_rinse_no_water_percent = C_mean_hot_rinse_no_water/Constants.sigma_alkaline
        elif solution_type == Constants.other_keyword:
            C_mean_hot_rinse_no_water_percent = C_mean_hot_rinse_no_water/Constants.sigma_other

        logger.info(f"C_hotrinse (no water) = {C_mean_hot_rinse_no_water_percent} %")

        rinse_KPIs = {'C_avg hot rinse [mS/cm]':           C_mean_hot_rinse,
                      'C_avg hot rinse, no water [mS/cm]': C_mean_hot_rinse_no_water,
                      'C_avg hot rinse, no water [%]':     C_mean_hot_rinse_no_water_percent,
                      'Solution type':                     solution_type}

        logger.info(rinse_KPIs)
        return rinse_KPIs



class Blowout(LowCZoneMaskHandler):
    '''Class dealing with blowout phase, the last peak in F'''

    def __init__(self, var_instance):
        super().__init__(var_instance)


    def _find_blowout_peak(self, F_fraction = 30, blowout_threshold = 50):
        '''We define blowout as the first F peak after T_max. So, the peak of blowout is determined by seeing if
        there is a peak in F (not dF) after T_max is done. If F_peak after T_max > 50 (by Nienke), then we have blowout. 
        If not, then take the first F peak after T_max
        INPUT:
            - F_fraction: fraction of F above which we consider a peak
        OUTPUT:
            - blowout_peak_time: time of blowout peak
            - blowout_peak_idx: idx of blowout peak
            - is_there_blowout_peak: 0/1 value'''

        F_threshold         = self.Variables.F_max / F_fraction
        F_peaks_idx, _      = find_peaks(self.Variables.F_values, height = F_threshold)
        F_peaks_after_T_max = F_peaks_idx[F_peaks_idx > self.Variables.T_max_idx]

        if F_peaks_after_T_max.size:
            F_peaks_val_after_T_max = self.Variables.F_values[F_peaks_after_T_max]
            F_peaks_above_threshold = F_peaks_val_after_T_max[F_peaks_val_after_T_max.values > blowout_threshold]
            
            if F_peaks_above_threshold.size:
                blowout_peak_idx      = F_peaks_above_threshold.index[0]
                is_there_blowout_peak = 1
            else:
                blowout_peak_idx      = F_peaks_after_T_max[0] # 1st peak after T_max is blowout
                is_there_blowout_peak = 1

            blowout_peak_time = self.Variables.t_values[blowout_peak_idx]
            logger.info(f"Blowout exists, peak is @ {blowout_peak_time}, idx {blowout_peak_idx}")
            return blowout_peak_time, blowout_peak_idx, is_there_blowout_peak
        else:
            logger.warning("Cannot find blowout peak")
            return None, None, is_there_blowout_peak


    def _find_blowout_start_and_stop(self, blowout_peak_idx):
    # def _find_blowout_start(self):
        '''Blowout is the large peak in F after T_max
        This function first sees if there are dF peaks after postrinse and takes the fist one as blowout. If not, then it sees if there are
        dF peaks during postrinse and takes the first as blowout. If not, then it checks if the last dF peak occurs before end of postrinse,
        and if it does, then it returns None
        INPUT: -
        OUTPUT:
            - blowout_start_time: start time of blowout phase
            - blowout_start_idx: start idx of blowout phase
            - is_there_blowout: 0/1 value to denote whether blowout was detected'''

        left_stop_index  = blowout_peak_idx
        right_stop_index = blowout_peak_idx

        while (left_stop_index > 0) and self.Variables.F_values[left_stop_index] > self.Variables.F_values[left_stop_index - 1]:
            left_stop_index -= 1
        while (right_stop_index < len(self.Variables.F_values) - 1) and self.Variables.F_values[right_stop_index] > self.Variables.F_values[right_stop_index + 1]:
            right_stop_index += 1
        
        blowout_start_idx  = left_stop_index
        blowout_stop_idx   = right_stop_index
        blowout_start_time = self.Variables.t_values[blowout_start_idx]
        blowout_stop_time  = self.Variables.t_values[blowout_stop_idx]
        logger.info(f"Blowout starts @ {blowout_start_time}, idx {blowout_start_idx}, ends @ {blowout_stop_time}, idx {blowout_stop_idx}")

        return blowout_start_time, blowout_start_idx, blowout_stop_time, blowout_stop_idx
    
        # ==============
        # dF_max_after_T_max = self.Variables.dF_relative_max_time[self.Variables.dF_relative_max_time > self.Variables.T_max]
        # dF_max_after_postrinse_end   = self.Variables.dF_relative_max_time[self.Variables.dF_relative_max_time >= self.Variables.T_max]
        # is_there_blowout: int        = 0

        # if len(dF_max_after_T_max):
        #     blowout_start_time = dF_max_after_T_max.values[0] # first value
        #     logger.info("Last dF peak is after end of postrinse, so can detect blowout")
        #     is_there_blowout = 1
        # elif len(dF_max_after_T_max):
        #     blowout_start_time = dF_max_after_T_max.values[0] # first value
        #     logger.info("Cannot find dF peaks after end of postrinse, but can find after start of postrinse")
        #     is_there_blowout = 1 # unsure about this
        #     # maybe see if blowout peak is after this blowout_start_time and if so, then we have blowout, but if not then no blowout
        # else:
        #     # !!! unsure if the following block should exist!!!
        #     # the following line gives errors because: IndexError: index -1 is out of bounds for axis 0 with size 0

        #     # if self.Variables.dF_relative_max_time.values[-1] < postrinse_end_time:
        #     #     logger.warning("Last dF peak is before end of postrinse, so cannot detect blowout")
        #     #     is_there_blowout = 0
        #     return postrinse_end_time, postrinse_end_idx, is_there_blowout

        # if blowout_start_time:
        #     blowout_start_idx = np.where(self.Variables.t_values == blowout_start_time)[0][0]
        #     logger.info(f"Blowout is @ {blowout_start_time}, idx {blowout_start_idx}")

        # return blowout_start_time, blowout_start_idx, is_there_blowout


    # remove when the substitute method works
    def _find_blowout_end(self, postrinse_time, postrinse_end_time, postrinse_end_idx, blowout_start_time):
        '''This function deals with finding the end of the blowout period, which is the little peak in F after the postrinse is fully completed
        The blowout is an increase in F (dF peak), which reaches a maximum (dF=0) then decreases (dF drop).
        So the end of blowout is characterized by a drop in dF'''

        blowout_start_time, blowout_start_idx, is_there_blowout   = self._find_blowout_start(postrinse_time, postrinse_end_time, postrinse_end_idx)
        blowout_peak_time, blowout_peak_idx, is_there_blowout_peak= self._find_blowout_peak(F_fraction = 30, blowout_threshold = 50)

        if is_there_blowout:
            dF_min_after_blowout_start = self.Variables.dF_relative_min_time[self.Variables.dF_relative_min_time > blowout_start_time]
            logger.debug(dF_min_after_blowout_start)

            if len(dF_min_after_blowout_start):
                blowout_end_time = dF_min_after_blowout_start.values[0] #first DROP since blowout
                blowout_end_idx  = np.where(self.Variables.t_values == blowout_end_time)[0][0]
                logger.info(f'Blowout end @ {blowout_end_time}, idx{blowout_end_idx}')
                return blowout_end_time, blowout_end_idx
            else:
                if is_there_blowout_peak == 0:
                    logger.debug('Cannot find end AND peak of blowout, so it does not exist')
                    return None, None
                else:
                    logger.info('Peak exists, but cannot find the end of blowout, so will calculate it')
                    blowout_duration = 2*(blowout_peak_time - blowout_start_time)
                    blowout_end_time = blowout_start_time + blowout_duration
                    blowout_end_idx  = np.where(self.Variables.t_values == blowout_end_time)[0][0]
                    logger.info(f'Blowout end @ {blowout_end_time}, idx{blowout_end_idx}')
                    return blowout_end_time, blowout_end_idx
        else:
            return None, None


    # def find_blowout_duration(self, postrinse_time, postrinse_end_time, postrinse_end_idx):
    def find_blowout_duration(self):
        '''If we have blowout start and end, then get its duration by subtracting the two values
        INPUT: -
        OUTPUT: blowout_duration'''

        # blowout_peak_time, blowout_peak_idx, is_there_blowout_peak = self._find_blowout_peak(F_fraction = 30, blowout_threshold = 50)
        # blowout_start_time, blowout_idx, is_there_blowout = self._find_blowout_start(postrinse_time, postrinse_end_time, postrinse_end_idx)
        # blowout_end_time, blowout_end_idx                 = self._find_blowout_end(postrinse_time, postrinse_end_time, postrinse_end_idx, blowout_start_time)

        _, blowout_peak_idx, is_there_blowout_peak = self._find_blowout_peak(30, 50)
        
        if is_there_blowout_peak:
            blowout_start_time, blowout_start_idx, blowout_stop_time, blowout_stop_idx = self._find_blowout_start_and_stop(blowout_peak_idx)
        else:
            logger.debug(f'Cannot find blowout, returning 0')
            return 0

        blowout_duration_s = (blowout_stop_time - blowout_start_time).total_seconds()
        logger.debug(f'Blowout lasts {blowout_duration_s}s')
        return blowout_duration_s

        if is_there_blowout and is_there_blowout_peak:
            logger.debug(f"{blowout_start_time}, {type(blowout_start_time)}")
            logger.debug(f"{blowout_end_time}, {type(blowout_end_time)}")
            blowout_duration = blowout_end_time - blowout_start_time

            logger.debug(f"{blowout_duration}, {type(blowout_duration)}")

            blowout_duration_s = pd.to_timedelta(blowout_duration).total_seconds()
            logger.debug(f'Blowout lasts {blowout_duration_s}s')
            return blowout_duration_s
        else:
            logger.debug(f'Cannot find blowout, returning 0')
            return 0

