
import csv
from dataclasses import dataclass
import os
# import openpyxl

import config_info_obtainer as ci
from logging_maker import logger


# remove this class if csv class works well
class ExcelSheetMaker:
    '''Class that makes the output Excel sheet'''

    excel_extension = '.xlsx'

    def __init__(self, workbook_name, resulting_phases, filename):
        self.workbook_name : str  = workbook_name
        self.open_workbook        = [] #openpyxl.Workbook() #create workbook
        self.active_worksheet     = [] #self.open_workbook.active #select active worksheet

        self.filename      : str  = filename
        self.header_row_number:int= 1 # smallest value Excel rows can have
        self.header_exists : int  = 0
        self.loaded_file   : int  = None

        self.post_milk_flush_time = resulting_phases.post_milk_flush_time #this is from main
        self.post_milk_flush_idx  = resulting_phases.post_milk_flush_idx
        self.prerinse_time        = resulting_phases.prerinse_time
        self.prerinse_idx         = resulting_phases.prerinse_idx
        self.low_C_zone_KPIs      = resulting_phases.low_C_zone_KPIs
        self.hot_rinse_time       = resulting_phases.hot_rinse_time
        self.hot_rinse_idx        = resulting_phases.hot_rinse_idx
        self.post_rinse_time      = resulting_phases.post_rinse_time
        self.post_rinse_idx       = resulting_phases.post_rinse_idx
        self.rinse_KPIs           = resulting_phases.rinse_KPIs

        self.header_values = ['File name',
                              'Day of measurement',
                              'Start of post-milk flush [RT]',
                              'Start of pre-rinse [RT]',
                              'Start of hot rinse [RT]',
                              'Time for max T [RT]',
                              'Start of post-rinse [RT]',
                              'Max T [C]',
                              f"Avg. T of {ci.Constants.time_interval}s interval with highest T [C]",
                              f"Duration for which T>{ci.Constants.T_crit}C [s]",
                              'Avg. C for hot rinse (with water) [mS/cm]', 
                              'Avg. C for hot rinse (no water) [mS/cm]',
                              'Avg. C for hot rinse (no water) [%]',
                              'Solution type']

        self.row_values = [self.filename,
                           self.post_milk_flush_time.strftime('%Y-%m-%d'),
                           self.post_milk_flush_time.time(),
                           self.prerinse_time.time(),
                           self.hot_rinse_time.time(),
                           Variables.T_max_time.time(),
                           self.post_rinse_time.time(),
                           Variables.T_max,
                           temp_abs_extrema['T of max time interval [C]'],
                           temp_abs_extrema['Duration for which T > T_crit [s]'],
                           self.rinse_KPIs['C_avg hot rinse [mS/cm]'],
                           self.rinse_KPIs['C_avg hot rinse, no water [mS/cm]'],
                           self.rinse_KPIs['C_avg hot rinse, no water [%]'],
                           solution_type,]


    def find_existing_excel_files(self):
        '''Find Excel files in directory'''

        os.chdir(ci.Constants.output_location)
        list_of_files_in_dir = os.listdir()

        excel_files_in_dir = []
        if list_of_files_in_dir: # if list of files NOT empty
            for file in list_of_files_in_dir:
                if file.endswith(self.excel_extension):
                    excel_files_in_dir.append(file)
        print("\n")
        logger.info(f"Existing Excel files: {excel_files_in_dir}")
        return excel_files_in_dir


    def remove_existing_excel_files(self, excel_files_in_dir):
        '''Remove existing Excel files in directory'''
        
        for file in excel_files_in_dir:
            os.remove(file)
            logger.info(f"Removed file: {file}")


    def create_new_excel_file(self):
        '''Create new Excel file'''

        self.open_workbook   = openpyxl.Workbook() # create workbook
        self.active_worksheet= self.open_workbook.active # select active worksheet
        logger.info("Created new Excel file")


    def load_existing_excel_file(self, excel_files_in_dir):
        '''Load existing Excel file in directory'''

        if excel_files_in_dir:
            excel_file           = excel_files_in_dir[0] #take the first file
            self.open_workbook   = openpyxl.load_workbook(excel_file)
            self.active_worksheet= self.open_workbook.active #select active worksheet
            logger.info(f"Loaded Excel file '{excel_file}'")
            self.loaded_file = 1
            return excel_file
        else:
            self.create_new_excel_file()
            logger.info(f"Did not find Excel file, so created {self.open_workbook}")
            self.loaded_file = 0


    def check_if_header_row_filled(self):
        '''Looking through the rows of the Excel sheet to see which row is available to place results in
           Judging whether a row is filled based on the first cell in it (so column 1 or A)'''
        
        column_num = 1
        if (self.active_worksheet.cell(row = self.header_row_number, column = column_num).value ) != None:
            logger.info(f"Header exists on row {self.header_row_number}")
            self.header_exists = 1
        else:
            self.header_exists = 0


    def fill_header(self):
        '''Fill header row with values'''

        if self.header_exists == 0:
            for col, value in enumerate(self.header_values, start = 1):
                self.active_worksheet.cell(row = self.header_row_number, column = col, value = value)
            logger.info(f"Created header in row {self.header_row_number}")
        else:
            logger.info(f"Header exists in row {self.header_row_number}, will not fill it")


    def find_available_row(self):
        '''Looping through the rows of the Excel sheet to see which row is available to place results in
           Judging whether a row is filled based on the first cell in it (so column 1 or A)'''
        
        row_number = 1 # smallest row number in Excel
        counter    = 0
        while True:
            if (self.active_worksheet.cell(row = row_number, column = 1).value ) == None:
                logger.info(f"Row {row_number} is available")
                return row_number
            else:
                row_number += 1
                counter    += 1
        
            if counter == 750:
                logger.critical(f"There are more than {counter} entries in the Excel sheet. Shutting down")
                break


    def fill_row_with_values(self, free_row_number):
        '''Fill row with values'''

        for i, val in enumerate(self.row_values, start = 1):
            self.active_worksheet.cell(row = free_row_number, column = i, value = val)
            print(i, val)

        logger.info(f"Filled row {free_row_number}")


    def save_workbook(self, excel_file):
        '''Save workbook to file. Saving depends on whether file was loaded or created'''

        if self.loaded_file == 0: # created file
            self.open_workbook.save(self.workbook_name)
            logger.info(f"Saved a new workbook '{self.workbook_name}'")
        elif self.loaded_file == 1: # loaded file
            self.open_workbook.save(excel_file)
            logger.info(f"Saved a loaded workbook '{excel_file}'")


    def close_workbook(self):
        '''Close workbook'''
        self.open_workbook.close()


    def make_excel_workbook(self, excel_file = None):
        '''Function that creates and saves the Excel workbook
        INPUT: header + cell values
        OUTPUT: None, creates and saves the excel file'''

        if excel_file:
            self.save_workbook(excel_file)
        else:
            self.save_workbook(self.workbook_name)

        self.close_workbook()


class csvFileMaker:
    '''Class that makes the CSV output file'''

    csv_extension = '.csv'

    # def __init__(self, output_file_name, resulting_phases, filename):
    def __init__(self, output_file_name, resulting_phases, input_filename, temp_abs_extrema, var_instance, solution_type):

        self.output_file_name: str= output_file_name
        self.filename        : str= input_filename

        self.post_milk_flush_time = resulting_phases.post_milk_flush_time #this is from main
        self.prerinse_time        = resulting_phases.prerinse_time
        self.prerinse_idx         = resulting_phases.prerinse_idx
        self.low_C_zone_KPIs      = resulting_phases.low_C_zone_KPIs
        self.hot_rinse_time       = resulting_phases.hot_rinse_time
        self.hot_rinse_idx        = resulting_phases.hot_rinse_idx
        self.post_rinse_time      = resulting_phases.postrinse_time
        self.post_rinse_idx       = resulting_phases.postrinse_idx
        self.rinse_KPIs           = resulting_phases.rinse_KPIs
        self.blowout_duration     = resulting_phases.blowout_duration
        self.low_C_zone_start_time= resulting_phases.low_C_zone_start_time
        self.zone_duration_s      = resulting_phases.zone_duration_s


        self.header_values = ['File name',
                              'Day of measurement',
                              'Start of post-milk flush [RT]',
                              'Start of pre-rinse [RT]',
                              'Start of hot rinse [RT]',
                              'Time for max T [RT]',
                              'Start of post-rinse [RT]',
                              'Start of low-C zone [RT]',
                              'Duration of low-C zone [s]',
                              'Max T [C]',
                              f"Avg. T of {ci.Constants.time_interval}s interval with highest T [C]",
                              f"Duration for which T>{ci.Constants.T_crit}C [s]",
                              'Avg. C for hot rinse (with water) [mS/cm]', 
                              'Avg. C for hot rinse (no water) [mS/cm]',
                              'Avg. C for hot rinse (no water) [%]',
                              'Blowout duration [s]',
                              'Solution type',]

        self.row_values = [self.filename,
                           self.post_milk_flush_time.strftime('%Y-%m-%d'),
                           self.post_milk_flush_time.time(),
                           self.prerinse_time,
                           self.hot_rinse_time.time(),
                           var_instance.T_max_time.time(),
                           self.post_rinse_time.time(),
                           resulting_phases.low_C_zone_start_time.time(),
                           resulting_phases.zone_duration_s,
                           var_instance.T_max,
                           temp_abs_extrema['T of max time interval [C]'],
                           temp_abs_extrema['Duration for which T > T_crit [s]'],
                           self.rinse_KPIs['C_avg hot rinse [mS/cm]'],
                           self.rinse_KPIs['C_avg hot rinse, no water [mS/cm]'],
                           self.rinse_KPIs['C_avg hot rinse, no water [%]'],
                           self.blowout_duration,
                           solution_type,]


    def create_empty_csv_if_nonexistent(self):
        '''Find CSV files in directory'''

        os.chdir(ci.Constants.output_location)
        list_of_files_in_dir = os.listdir()

        if self.output_file_name in list_of_files_in_dir:
            logger.info(f"Found existing CSV file of same name")
        else:
            logger.info(f"Did not find CSV file of same name, creating one...")
            with open(self.output_file_name, 'w', newline='') as file:
                pass # to create a file without creating an empty row


    def check_if_header_row_filled(self):
        '''Looking if there exists a header row
           Judging whether the header exists based on whether item 1 of the header exists in the csv file'''
        
        with open(self.output_file_name, 'r') as file:
            if self.header_values[0] in file.read():
                logger.info("Header exists")
                self.header_exists = 1
            else:
                logger.info("Header does not exist")
                self.header_exists = 0


    def fill_header(self):
        '''Fill header row with values'''

        if self.header_exists == 0:
            with open(self.output_file_name, 'a', newline = '') as csvfile:
                writer = csv.writer(csvfile, delimiter = ';')
                writer.writerow(self.header_values)
            logger.info(f"Created header")
        else:
            logger.info(f"Header exists, will not fill it")


    def write_to_csv_file(self):
        with open(self.output_file_name, 'a', newline = '') as csvfile:
            writer = csv.writer(csvfile, delimiter = ';')
            writer.writerow(self.row_values) # Write the specified data to the CSV file

            logger.info(f"{self.row_values}")


class InputCSVFilesSolutionObtainer:
    '''Class that counts # of input CSV files and obtains the solution type from each filename'''

    def obtain_input_file_names(extension = '.csv'):
        '''Counts the number of csv files'''
        
        input_file_location = ci.Constants.input_location
        os.chdir(input_file_location)
        list_of_files_in_dir = os.listdir()

        list_of_input_files = []
        for file in list_of_files_in_dir:
            if file.endswith(extension):
                list_of_input_files.append(file)

        return list_of_input_files


    def obtain_solution_type_from_filename(input_filename, config_info):
        '''Get solution type from file name'''

        if config_info['alkaline_keyword'] in input_filename.lower():
            solution_type = config_info['alkaline_keyword']
            logger.info(f"Solution is {config_info['alkaline_keyword']}")

        elif config_info['acid_keyword'] in input_filename.lower():
            solution_type = config_info['acid_keyword']
            logger.info(f"Solution is {config_info['acid_keyword']}")

        elif config_info['other_keyword'] in input_filename.lower():
            solution_type = config_info['other_keyword']
            logger.info(f"Solution is {config_info['other_keyword']}")
        else:
            solution_type = 'UNKNOWN'
            logger.info(f"Solution is {solution_type}")


        logger.info(f"File '{input_filename}' is of type '{solution_type}'")
        return solution_type
