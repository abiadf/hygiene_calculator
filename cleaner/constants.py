
class DfConstants:
    '''Class of 'Constants' where we keep dataframe constants. These constants are not to be changed'''

    excel_temperature_column = '4AI 1043 - Temperature [°C]'
    excel_conductivity_column= 'bueS-X-Gateway - Cond_compensated [mS/cm]' #Constants.C_column_name
    excel_flow_column        = 'bueS-X-Gateway - Flow_switched [l/min]' #Constants.F_column_name
    excel_time_column        = 'Time' # Constants.time_column_name

    df_time_column           = 'Time [RT]'
    df_temperature_column    = 'Temperature [C]'
    df_conductivity_column   = 'Conductivity [mS/cm]'
    df_flow_column           = 'Flow [L/min]'

    time_substring           = 'time'
    temperature_substring    = 'temp'
    conductivity_substring   = 'cond'
    flow_substring           = 'flow'
