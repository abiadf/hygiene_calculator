'''Module that reads info from config file and converts it into a class. It runs the functions/classes, then logs the contents of the config file'''

import ast
import configparser
import os

from logging_maker import logger

class ConfigFileReader():
    '''This class gets info from config file and turns it into string type, stored in a dict'''

    def obtain_info_from_config(self):
        '''Get info from config.ini file'''

        code_path = r'C:\consumables_cleaning\new_structure'
        os.chdir(code_path)

        list_of_files        = os.listdir()
        config_file_extension= '.ini'

        config_file_list = [item for item in list_of_files if config_file_extension in item]
        config_file      = ''.join(config_file_list)
        config_parser    = configparser.ConfigParser()
        config_parser.read(config_file)

        # Extract info from config file AS STRING
        file_section           = 'File'
        input_location_str     = config_parser.get(file_section, 'input_location')
        output_location_str    = config_parser.get(file_section, 'output_location')

        columns_section        = 'Columns'
        temperature_column_str = config_parser.get(columns_section, 'temperature_column')
        conductivity_column_str= config_parser.get(columns_section, 'conductivity_column')
        flow_column_str        = config_parser.get(columns_section, 'flow_column')
        time_column_str        = config_parser.get(columns_section, 'time_column')

        types_section          = 'Types'
        alkaline_keyword_str   = config_parser.get(types_section, 'alkaline_keyword')
        acid_keyword_str       = config_parser.get(types_section, 'acid_keyword')
        other_keyword_str      = config_parser.get(types_section, 'other_keyword')

        constants_section      = 'Constants'
        T_crit_str             = config_parser.get(constants_section, 'T_crit')
        time_crit_str          = config_parser.get(constants_section, 'time_crit')
        sigma_alkaline_str     = config_parser.get(constants_section, 'sigma_alkaline')
        sigma_acid_str         = config_parser.get(constants_section, 'sigma_acid')
        sigma_other_str        = config_parser.get(constants_section, 'sigma_other')
        t_cond_water_str       = config_parser.get(constants_section, 't_cond_water')

        logger.info("Successfully obtained info from config.ini file")

        config_info_str = { 
                          'input_location_str':      input_location_str,
                          'output_location_str':     output_location_str,
                          'temperature_column_str':  temperature_column_str,
                          'conductivity_column_str': conductivity_column_str,
                          'flow_column_str':         flow_column_str,
                          'time_column_str':         time_column_str,
                          'alkaline_keyword_str':    alkaline_keyword_str,
                          'acid_keyword_str':        acid_keyword_str,
                          'other_keyword_str':       other_keyword_str,
                          'T_crit_str':              T_crit_str,
                          'time_crit_str':           time_crit_str,
                          'sigma_alkaline_str':      sigma_alkaline_str,
                          'sigma_acid_str':          sigma_acid_str,
                          'sigma_other_str':         sigma_other_str,
                          't_cond_water_str':        t_cond_water_str,
                          }

        return config_info_str


    def revert_config_info_type_from_str(self):
        '''Convert to literal type from STRING'''
        
        config_info_str = self.obtain_info_from_config()

        try:
            input_location      = ast.literal_eval(config_info_str['input_location_str'])
            output_location     = ast.literal_eval(config_info_str['output_location_str'])
            temperature_column  = ast.literal_eval(config_info_str['temperature_column_str'])
            conductivity_column = ast.literal_eval(config_info_str['conductivity_column_str'])
            flow_column         = ast.literal_eval(config_info_str['flow_column_str'])
            time_column         = ast.literal_eval(config_info_str['time_column_str'])
            alkaline_keyword    = ast.literal_eval(config_info_str['alkaline_keyword_str'])
            acid_keyword        = ast.literal_eval(config_info_str['acid_keyword_str'])
            other_keyword       = ast.literal_eval(config_info_str['other_keyword_str'])
            T_crit              = ast.literal_eval(config_info_str['T_crit_str'])
            time_crit           = ast.literal_eval(config_info_str['time_crit_str'])
            sigma_alkaline      = ast.literal_eval(config_info_str['sigma_alkaline_str'])
            sigma_acid          = ast.literal_eval(config_info_str['sigma_acid_str'])
            sigma_other         = ast.literal_eval(config_info_str['sigma_other_str'])
            t_cond_water        = ast.literal_eval(config_info_str['t_cond_water_str'])

            logger.info("Successfully turned config file into string type")

        except: # if something goes wrong, ie: cannot find file
            input_location      = "C:\\consumables_cleaning\\input\\"
            output_location     = "C:\\consumables_cleaning\\output\\"
            temperature_column  = '4AI 1043 - Temperature [°C]'
            conductivity_column = 'bueS-X-Gateway - Cond_compensated [mS/cm]'
            flow_column         = 'bueS-X-Gateway - Flow_switched [l/min]'
            time_column         = 'Time'
            alkaline_keyword    = 'alkaline'
            acid_keyword        = 'acid'
            other_keyword       = 'other'
            T_crit              = 72
            time_crit           = 120
            sigma_alkaline      = 23.6
            sigma_acid          = 7.24
            sigma_other         = 30
            t_cond_water        = 20

            logger.error("Cannot access .ini file, using manual input")
            logger.error("Make sure there is NO single %% sign at once")

        config_info = { 
                      'input_location':   input_location,
                      'output_location':  output_location,
                      'T_column_name':    temperature_column,
                      'C_column_name':    conductivity_column,
                      'F_column_name':    flow_column,
                      'time_column_name': time_column,
                      'alkaline_keyword': alkaline_keyword,
                      'acid_keyword':     acid_keyword,
                      'other_keyword':    other_keyword,
                      'T_crit':           T_crit,
                      'time_interval':    time_crit,
                      'sigma_alkaline':   sigma_alkaline,
                      'sigma_acid':       sigma_acid,
                      'sigma_other':      sigma_other,
                      't_cond_water':     t_cond_water,
                      }
        
        return config_info


class Dict2ClassConverter:
    '''This class gets info from the last class (in dict) and converts its info to class'''

    def __init__(self, dictionary):
        self.__dict__.update(dictionary)


def run_config_file_reader():
    '''Run the code about extracting info from config file'''
    
    config_file_reader = ConfigFileReader()
    config_info        = config_file_reader.revert_config_info_type_from_str()

    Constants               = Dict2ClassConverter(config_info)
    list_of_config_variables= [name for name in dir(Constants) if not callable(getattr(Constants, name)) and not name.startswith('__')]

    return Constants, list_of_config_variables, config_info


def log_config_info(Constants, list_of_config_variables):
    '''Function that when executed, logs key info
    INPUT: Constants class, list_of_config_variables (list of variables)
    OUTPUT: -, this function only logs'''

    logger.info(f"************************")
    logger.info(f"List of variables: ")
    logger.info(list_of_config_variables)
    logger.info(f"Input File location: {Constants.input_location}")
    logger.info(f"Output location: {Constants.output_location}")
    logger.info(f"Columns: {Constants.T_column_name} | {Constants.C_column_name} | {Constants.F_column_name}, {Constants.time_column_name}")
    logger.info(f"T crit [C]: {Constants.T_crit}")
    logger.info(f"t crit [s]: {Constants.time_interval}")
    logger.info(f"Sigma [mS/cm]: {Constants.sigma_alkaline} (alkaline), {Constants.sigma_acid} (acid), {Constants.sigma_other} (other)")
    logger.info(f"Time crit water [s]: {Constants.t_cond_water}")


Constants, list_of_config_variables, config_info = run_config_file_reader()
log_config_info(Constants, list_of_config_variables)
