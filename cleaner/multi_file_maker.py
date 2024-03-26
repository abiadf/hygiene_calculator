
import csv
from dataclasses import dataclass
import os
import openpyxl
import numpy as np
from sys import exit

import config_info_obtainer as ci
from data_cleaner import DataCleaner, DerivativeMaker
from input_output_file_handler import ExcelSheetMaker, csvFileMaker, InputCSVFilesSolutionObtainer
from logging_maker import logger
from phase_identifier import PrerinsePostmilkflushFinder, Blowout, PostRinseFinder, LowCZoneMaskHandler, EarlyCmaxHandler, LowCZoneAndHotrinseFinder
# from phase_identifier_results import ResultingPhases
from run_tempKPI_derivative import run_data_cleaning_temperature_and_derivative_classes
from utils import ColumnFinder


list_of_input_file_names = InputCSVFilesSolutionObtainer.obtain_input_file_names()


for input_filename in list_of_input_file_names:
    solution_type = InputCSVFilesSolutionObtainer.obtain_solution_type_from_filename(input_filename, ci.config_info)
    
    df_removed_first_pt, df_diff_smooth, df_diff2_smooth, df_diff_clipped, \
    df_temp_rel_extrema, temp_abs_extrema, dY_absolute_extrema, dY_relative_extrema = run_data_cleaning_temperature_and_derivative_classes(input_filename)
    
    logger.info(f"File is called: {input_filename.upper()}")
    
    @dataclass
    class Variables():
        '''Place to store variables to use throughout the code'''
        
        df      = df_removed_first_pt.copy()
        dYdx, _ = DerivativeMaker.make_derivatives(df) # Get derivatives
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
        dC_max_val     = dC_values[dC_max_idx]
        
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
        C_mean       = C_values.mean()

        F_max        = np.amax(F_values)

    var_instance = Variables()


    class ResultingPhases():
    
        def __init__(self, solution_type):

            low_C_hot_rinse_finder   = LowCZoneMaskHandler(var_instance)
            self.dC_mask_low_std     = low_C_hot_rinse_finder.apply_std_mask_on_dC(roll_window_size = 3, max_std_threshold_fraction = 0.1)
            self.dC_mask_T_max       = low_C_hot_rinse_finder.apply_T_max_mask_on_dC(self.dC_mask_low_std)
            self.dC_mask_C_percentile= low_C_hot_rinse_finder.apply_C_percentile_mask_on_dC(self.dC_mask_T_max, percentile_crit = 40)
            
            early_C_max_handler        = EarlyCmaxHandler(var_instance)
            self.is_there_early_large_C= early_C_max_handler.detect_if_early_C_max_exists(large_C_search_time_fraction_threshold = 0.25)
            early_C_max_handler.smoothen_large_C_peak_values_if_it_exists(self.is_there_early_large_C)

            low_C_zone_finder    = LowCZoneAndHotrinseFinder(var_instance)
            self.low_C_zones     = low_C_zone_finder.group_low_C_zones(self.dC_mask_C_percentile)
            self.low_C_zone_start_time, self.low_C_zone_start_idx, self.zone_duration_s \
                                 = low_C_zone_finder.obtain_best_low_C_zone_candidate(self.low_C_zones)
            self.low_C_zone_KPIs = low_C_zone_finder.get_low_C_zone_KPIs(self.low_C_zone_start_time, self.low_C_zone_start_idx, self.zone_duration_s)
            self.hot_rinse_time, self.hot_rinse_idx \
                                 = low_C_zone_finder.find_hot_rinse_time(self.low_C_zone_KPIs, num_neighbors = 3, time_between_hotrinse_Tmax_in_min = 4)

            prerinse_postmilk_finder              = PrerinsePostmilkflushFinder(var_instance)
            self.prerinse_time, self.prerinse_idx = prerinse_postmilk_finder.find_prerinse_time(self.low_C_zone_start_time, self.hot_rinse_idx, time_between_prerinse_Tmax_in_min = 7, prerinse_hotrinse_limit_s = 200)
            self.post_milk_flush_time, self.post_milk_flush_idx= prerinse_postmilk_finder.find_postmilk_flush_time_depending_on_early_sharp_C(self.is_there_early_large_C, self.low_C_zone_start_time, self.hot_rinse_idx)

            postrinse                                       = PostRinseFinder(var_instance)
            self.postrinse_time, self.postrinse_idx         = postrinse.find_post_rinse_start_time(num_neighbors = 8, Tmax_postrinse_timeout_s = 60)
            self.post_rinse_end_time, self.postrinse_end_idx= postrinse.find_post_rinse_end_time(self.postrinse_time, num_neighbors = 8)
            self.rinse_KPIs                                 = postrinse.collect_rinse_KPIs(self.hot_rinse_idx, self.postrinse_idx, self.low_C_zone_KPIs, solution_type)

            blowout               = Blowout(var_instance)
            self.blowout_duration = blowout.find_blowout_duration()

    resulting_phases = ResultingPhases(solution_type)
    
    
    '''Send the data to csv/Excel files'''

    # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    # output_file_name  = 'output.xlsx'
    # excel_sheet_maker = ExcelSheetMaker(output_file_name, resulting_phases, input_filename)
    # excel_files_in_dir= excel_sheet_maker.find_existing_excel_files()
    # # excel_sheet_maker.remove_existing_excel_files(excel_files_in_dir)
    # excel_file        = excel_sheet_maker.load_existing_excel_file(excel_files_in_dir)
    # excel_sheet_maker.check_if_header_row_filled()
    # excel_sheet_maker.fill_header()
    # free_row_number   = excel_sheet_maker.find_available_row()
    # excel_sheet_maker.fill_row_with_values(free_row_number)
    # excel_sheet_maker.make_excel_workbook(excel_file)
    print("+++++++++++++++++++++++++++++++++++++")
    output_file_name = 'output.csv'
    # csv_file_maker   = csvFileMaker(output_file_name, resulting_phases, input_filename)
    csv_file_maker   = csvFileMaker(output_file_name, resulting_phases, input_filename, temp_abs_extrema, var_instance, solution_type)
    csv_file_maker.create_empty_csv_if_nonexistent()
    csv_file_maker.check_if_header_row_filled()
    csv_file_maker.fill_header()
    csv_file_maker.write_to_csv_file()
    print("=======================================")

