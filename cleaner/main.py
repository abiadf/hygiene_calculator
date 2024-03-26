'''Run everything'''

import os
import pandas as pd

os.system('cls')
pd.set_option('future.no_silent_downcasting', True) # prevents issues with future pd versions

# %% #1 - Extracting info from config file

# removed below, it is already used in multi_file_maker
# import config_info_obtainer

# %% #2 - temperature-KPIs AND derivative peaks

import multi_file_maker as mfm

list_of_input_files = mfm.InputCSVFilesSolutionObtainer.obtain_input_file_names()

for file in list_of_input_files:
    filename = file
    # put the rest of the stuff here

# %% #3 - Phase identifying class
# from phase_identifier_results import ResultingPhases

# resulting_phases = ResultingPhases() # is this line needed?
# pass this^ into the 'ExcelSheetMaker' class, used below

# %% #4 - Excel sheet and plot
# import run_excel_and_plot

# below line is not in use
from excel_handler import ExcelSheetMaker


# %% #5 - Plot

'''Uncomment the following when need to plot'''

# from plotting_functionality import PlotTemporaryGraphs, GraphsPlotter

# '''Run the plotting code'''
# # Variables to input into the vertical_lines function
# dY_max_idx     = dY_absolute_extrema[0]['dY_max idx [#]']
# dY_rel_max_idx = dY_relative_extrema[0]['Index of rel max']
# dY_rel_min_idx = dY_relative_extrema[0]['Index of rel min']

# plotInstance   = PlotTemporaryGraphs('t'.upper())
# # singleplot        = plotInstance.single_graph_plotter()
# # plot_T_crit_line  = plotInstance.plot_T_crit_line()
# # plot_vertical_line= plotInstance.plot_vertical_lines(dY_rel_max_idx, dY_rel_min_idx, dY_max_idx)
# # plot_rectangles   = plotInstance.plot_rectangles()
