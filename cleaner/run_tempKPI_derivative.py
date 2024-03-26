
import os
import pandas as pd

import config_info_obtainer as ci
from csv_to_df import csvToDataframeMaker
from data_cleaner import DataCleaner, DerivativeMaker
from derivative_peaks_finder import FindDerivativePeaks
from tempKPIs import TemperatureKPIObtainer


location = ci.Constants.input_location

def run_data_cleaning_temperature_and_derivative_classes(filename):
    '''Run the classes dealing with 1) cleaning code, 2) temperature-KPIs AND 3) derivative peaks'''

    os.chdir(location)
    csv_to_df_maker = csvToDataframeMaker(filename)
    df              = csv_to_df_maker.save_data_in_dataframe(ci.Constants.input_location)
    df_relevant     = csv_to_df_maker.make_dataframe_of_relevant_columns(df)

    data_cleaner        = DataCleaner()
    df_filled           = data_cleaner.fill_data_gaps(df_relevant)
    df_smooth           = data_cleaner.smoothen_data(df_filled, window_size = 5)
    df_removed_last_pt  = data_cleaner.remove_points_after_last_F_peak(df_smooth, points_after_last_F_peak_to_keep = 30, F_fraction_threshold = 40)
    df_removed_first_pt = data_cleaner.remove_initial_points(df_removed_last_pt, points_before_first_peak_to_keep = 20, fraction_threshold = 30)

    df_diff, df_diff2  = DerivativeMaker.make_derivatives(df_removed_first_pt, dx = 1)
    df_diff_smooth     = data_cleaner.smoothen_data(df_diff, window_size = 5)
    df_diff2_smooth    = data_cleaner.smoothen_data(df_diff2, window_size = 5)
    df_diff_clipped    = DerivativeMaker.clip_derivatives(df_diff, criterion = 0.005)

    tempKPI_Object      = TemperatureKPIObtainer(df_removed_first_pt)
    df_temp_rel_extrema = tempKPI_Object.calculate_temperature_relative_extrema(comparison_order = 30)
    temp_abs_extrema    = tempKPI_Object.calculate_temperature_absolute_extrema()

    find_derivative_peaks= FindDerivativePeaks(df_removed_first_pt)
    dY_absolute_extrema  = find_derivative_peaks.find_dY_absolute_extrema()
    dY_relative_extrema  = find_derivative_peaks.find_dY_relative_extrema(comparison_order = 30)

    return df_removed_first_pt, df_diff_smooth, df_diff2_smooth, df_diff_clipped, \
           df_temp_rel_extrema, temp_abs_extrema, dY_absolute_extrema, dY_relative_extrema
