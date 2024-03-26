
from excel_handler import ExcelSheetMaker
from plotting_functionality import PlotTemporaryGraphs, GraphsPlotter
import run_tempKPI_derivative as rpi


'''Make Excel sheet'''

excel_sheet_maker = ExcelSheetMaker('output.xlsx')
remove_excel = excel_sheet_maker.remove_existing_excel_file()
makeExcelFile= excel_sheet_maker.setup_excel_values()
makeExcel    = excel_sheet_maker.make_excel_workbook()


'''Run the plotting code'''

# Variables to input into the vertical_lines function
dY_max_idx        = rpi.dY_absolute_extrema[0]['dY_max idx [#]']
dY_rel_max_idx    = rpi.dY_relative_extrema[0]['Index of rel max']
dY_rel_min_idx    = rpi.dY_relative_extrema[0]['Index of rel min']

plotInstance      = PlotTemporaryGraphs('t'.upper())
# singleplot        = plotInstance.single_graph_plotter()
# plot_T_crit_line  = plotInstance.plot_T_crit_line()
# plot_vertical_line= plotInstance.plot_vertical_lines(dY_rel_max_idx, dY_rel_min_idx, dY_max_idx)
# plot_rectangles   = plotInstance.plot_rectangles()
