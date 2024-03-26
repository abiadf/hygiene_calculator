'''Module containing class that converts csv to usable DataFrame'''

import os
import pandas as pd

from config_info_obtainer import Constants
from constants import DfConstants
from logging_maker import logger


class csvToDataframeMaker:
    '''Gets data from file to dataframe, then keeps relevant columns (T, C, F) only'''

    def __init__(self, filename):
        self.filename = filename

    def save_data_in_dataframe(self, file_location) -> pd.core.frame.DataFrame:
        '''Read csv data of a certain file and save into pandas dataframe
        Input: filename (name of desired file)
        Output: dataframe of read file'''

        os.chdir(file_location)

        df = pd.read_csv(self.filename,
                         sep        = ";",
                         decimal    = ",",
                         quotechar  = "\"",
                        #  parse_dates= ["Time"])
                         converters = {"Time": pd.to_datetime})

        # df = df.set_index('Time') # Turns the nameless index column into a "Time" column

        input_dataframe: pd.core.frame.DataFrame = df
        return input_dataframe


    def make_dataframe_of_relevant_columns(self, input_dataframe) -> pd.core.frame.DataFrame:
        '''Makes new DataFrame of the relevant columns
        Input:  dataframe of the input csv file, contains all data
        Output: dataframe of the input csv file, contains relevant data only (time, T, C, F)'''

        relevant_columns   = [DfConstants.excel_time_column,
                              DfConstants.excel_temperature_column, 
                              DfConstants.excel_conductivity_column,
                              DfConstants.excel_flow_column]

        new_column_names   = {DfConstants.excel_time_column:         DfConstants.df_time_column,
                              DfConstants.excel_temperature_column:  DfConstants.df_temperature_column,
                              DfConstants.excel_conductivity_column: DfConstants.df_conductivity_column,
                              DfConstants.excel_flow_column:         DfConstants.df_flow_column}

        relevant_dataframe = input_dataframe[relevant_columns]
        output_dataframe   = relevant_dataframe.rename(columns = new_column_names)

        return output_dataframe


    # def obtain_solution_type_from_filename(self, config_info):
    #     '''Get solution type from file name'''

    #     if config_info['alkaline_keyword'] in (self.filename).lower():
    #         solution_type = config_info['alkaline_keyword']
    #         logger.info(f"Solution is {config_info['alkaline_keyword']}")

    #     elif config_info['acid_keyword'] in (self.filename).lower():
    #         solution_type = config_info['acid_keyword']
    #         logger.info(f"Solution is {config_info['acid_keyword']}")

    #     elif config_info['other_keyword'] in (self.filename).lower():
    #         solution_type = config_info['other_keyword']
    #         logger.info(f"Solution is {config_info['other_keyword']}")

    #     logger.info(f"File '{self.filename}' is of type '{solution_type}'")
    #     return solution_type
