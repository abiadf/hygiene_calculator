
import logging

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

from config_info_obtainer import Constants
import phase_identifier_results as rpi
from run_tempKPI_derivative import df_diff_smooth, df_diff2_smooth
# from variables import Variables

logging.getLogger('matplotlib').setLevel(logging.ERROR)
# mpl.rcParams['verbose.level'] = 'error'
# mpl.rcParams['figure.max_open_warning'] = 0  # This line suppresses the specific message you mentioned
# mpl.getLogger().setLevel(mpl.cbook._print_warning.level)



'''Class of plotting functionality'''

plot_properties    = {'T': ['T', '#fd6600', 'T [C]'     ], \
                      'C': ['C', 'g',       'C [mS/cm]' ], \
                      'F': ['F', '#69A3D8', 'F [L/min]' ] }

which_param_to_plot= {'T': 1, '1': '1', \
                      'C': 2, '2': '1', \
                      'F': 3, '3': '1'}


# THE FOLLOWING CLASSES ARE NOT IN USE YET
class PlotTemporaryGraphs():

    COMPARISON_ORDER = 15 #comparing neighbors to find local min/max points
    WINDOW_SIZE      = 3  #window for smoothing using pandas roll() method

    def __init__(self, param_initial: str):
        self.plot_properties= plot_properties
        self.filename       = Constants.filename
        self.param_initial  = param_initial
        self.param_to_plot  = which_param_to_plot[param_initial]
        # ===========================
        self.property_1st_letter= None
        self.time_index  = Variables.t_values
        self.Y           = Variables.parameters_dict[param_initial]
        self.dY          = df_diff_smooth.iloc[:, self.param_to_plot]
        self.d2Y         = df_diff2_smooth.iloc[:, self.param_to_plot]
        # ===========================
        self.fig, self.ax= plt.subplots()   #culprit for why a blank graph is made

    def single_graph_plotter(self):
        '''Makes the plot for a given property, like temp, cond, flow'''
        
        self.property_1st_letter = self.param_initial 
        
        plot_title = plot_properties[self.property_1st_letter][0]
        plot_color = plot_properties[self.property_1st_letter][1]
        plot_ylabel= plot_properties[self.property_1st_letter][2]
        plot_xlabel= 'Time [s]'
        width_inch = 12
        height_inch= 8
        self.fig.set_size_inches(width_inch, height_inch)
        self.fig.tight_layout(pad = 3)

        self.ax.title.set_text(f'{plot_title} vs. time')
        self.ax.set_ylabel(plot_ylabel)
        self.ax.set_xlabel(plot_xlabel)

        # Gridlines
        self.ax.grid(which='major', alpha=0.6)
        self.ax.grid(which='minor', alpha=0.15, color='gray', linestyle='-.')
        minor_locator_y = MultipleLocator(5)
        minor_locator_x = MultipleLocator(.05)
        self.ax.yaxis.set_minor_locator(minor_locator_y)
        self.ax.xaxis.set_minor_locator(minor_locator_x)
        self.fig.gca()

        # Plot itself
        self.ax.plot(self.time_index, self.Y, color = plot_color)
        # self.ax.plot(list(Variables().t_values.index.values), self.Y, color = plot_color)
        dY_zoom  = 0.5 * max(self.Y) / max(abs(self.dY))
        d2Y_zoom = 0.25* max(self.Y) / max(abs(self.d2Y))
        self.ax.plot(self.time_index, self.dY  * dY_zoom,  color = 'r')
        self.ax.plot(self.time_index, self.d2Y * d2Y_zoom, color = 'k')

        what_param_is_plotted = self.param_initial
        self.ax.legend([what_param_is_plotted,
                        f"d{what_param_is_plotted} ({dY_zoom:.2f}x zoom)",
                        f"d2{what_param_is_plotted}  ({d2Y_zoom:.2f}x zoom)"])

        self.fig.canvas.draw()

    def plot_T_crit_line(self) -> None:
        # self.ax.axhline(y = 0, color = '#FBF1CF', linestyle = '-')  # horizontal 0 line
        if self.property_1st_letter == 'T':
            self.ax.axhline(y = Constants.T_crit, color = '#ffb6c1', linestyle = '-') # horizontal line for T=72, only if plotting T

    def plot_vertical_lines(self, dY_relative_max_idx: np.ndarray, dY_relative_min_idx: np.ndarray, dY_max_idx: np.int64) -> None:
        '''Plots vertical lines for plot, such as maximum T and maxima in derivatives'''

        # Drawing a line for highest derivative
        self.ax.axvline(x = self.time_index[dY_max_idx], color = 'g', linestyle = '-.')

        # Drawing a line for maxima in dY for all properties
        for i in dY_relative_max_idx:
            self.ax.axvline(x = self.time_index[i], color = '#e28c1f', linestyle = ':')

        # Drawing a line for minima in dY for all properties, but only after maximum temperature
        for j in dY_relative_min_idx:
            if (self.time_index[j] > Variables.T_max_time):
                self.ax.axvline(x = self.time_index[j], color = '#026a81', linestyle = ':')

        x_caption         = 0.01
        y_caption_note    = 0.03
        y_caption_filename= 0.05
        self.fig.text(x_caption, y_caption_note,     "Not to scale",     fontsize = 10)
        self.fig.text(x_caption, y_caption_filename, Constants.filename, fontsize = 10)

        self.ax.axvline(x = rpi.post_milk_flush_time, color = 'k',       linestyle = '-')
        self.ax.axvline(x = rpi.prerinse_time,        color = 'g',       linestyle = '-')
        self.ax.axvline(x = rpi.hot_rinse_time,       color = 'b',       linestyle = '-')
        self.ax.axvline(x = Variables.T_max_time, color = '#A020F0', linestyle = '-.')
        self.ax.axvline(x = rpi.post_rinse_time,      color = 'r',       linestyle = '-')
        self.ax.axvline(x = rpi.post_milk_flush_time, color = 'k',       linestyle = '-')

    def plot_rectangles(self) -> None:
        '''Adds rectangles corresponding to each phase into the plot'''

        rect_transparency = 0.15
        plt.fill_between((rpi.post_milk_flush_time, rpi.prerinse_time),   0, max(self.Y), facecolor= "green", alpha = rect_transparency)
        plt.fill_between((rpi.prerinse_time,        rpi.hot_rinse_time),  0, max(self.Y), facecolor= "blue",  alpha = rect_transparency)
        plt.fill_between((rpi.hot_rinse_time,       rpi.post_rinse_time), 0, max(self.Y), facecolor= "red",   alpha = rect_transparency)

        plt.show() # plots the graph, only use at last function


# The following class is to replace the one above, since Nienke is not interested in vertical lines.
class GraphsPlotter():
    '''Class that makes plots to save''' 

    COMPARISON_ORDER = 15 #comparing neighbors to find local min/max points
    WINDOW_SIZE      = 3  #window for smoothing using pandas roll() method

    PLOT_PROPERTIES  = {'T': ['T', '#fd6600', 'T [C]'     ], \
                        'C': ['C', 'g',       'C [mS/cm]' ], \
                        'F': ['F', '#69A3D8', 'F [L/min]' ] }

    WHICH_PARAM_TO_PLOT= {'T': 1, '1': '1', \
                          'C': 2, '2': '1', \
                          'F': 3, '3': '1'}


    def __init__(self, param_initial: str):
        self.plot_properties= GraphsPlotter.PLOT_PROPERTIES
        self.filename       = Constants.filename
        self.param_initial  = param_initial
        self.param_to_plot  = GraphsPlotter.WHICH_PARAM_TO_PLOT[param_initial]
        # ===========================
        self.property_1st_letter= None
        self.time_index  = Variables.t_values
        self.Y           = Variables.parameters_dict[param_initial]
        # ===========================
        self.fig, self.ax= plt.subplots()   #culprit for why a blank graph is made


    def single_graph_plotter(self):
        '''Makes the plot for a given property, like temp, cond, flow'''
        
        self.property_1st_letter = self.param_initial 
        
        plot_title = GraphsPlotter.PLOT_PROPERTIES[self.property_1st_letter][0]
        plot_color = GraphsPlotter.PLOT_PROPERTIES[self.property_1st_letter][1]
        plot_ylabel= GraphsPlotter.PLOT_PROPERTIES[self.property_1st_letter][2]
        plot_xlabel= 'Time [s]'
        width_inch = 12
        height_inch= 8
        self.fig.set_size_inches(width_inch, height_inch)
        self.fig.tight_layout(pad = 3)

        self.ax.title.set_text(f'{plot_title} vs. time')
        self.ax.set_ylabel(plot_ylabel)
        self.ax.set_xlabel(plot_xlabel)

        # Gridlines
        self.ax.grid(which='major', alpha=0.6)
        self.ax.grid(which='minor', alpha=0.15, color='gray', linestyle='-.')
        # minor_locator_y = MultipleLocator(5)
        # minor_locator_x = MultipleLocator(.1)
        # self.ax.yaxis.set_minor_locator(minor_locator_y)
        # self.ax.xaxis.set_minor_locator(minor_locator_x)
        self.fig.gca()

        # Plot itself
        x_values_seconds = list(range(1024))
        from datetime import timedelta
        x_tick_labels = [timedelta(seconds=sec) for sec in x_values_seconds]
        self.ax.plot(x_values_seconds, self.Y, color = plot_color)
        plt.xticks(x_values_seconds, x_tick_labels)
# STOPPED HERE, NEED TO MAKE X-AXIS SECONDS, FROM 0 TO 1024


        # self.ax.plot(self.time_index, self.Y, color = plot_color)
        # Variables.df_indices

        what_param_is_plotted = self.param_initial
        self.ax.legend(what_param_is_plotted)

        self.fig.canvas.draw()


    def plot_T_crit_line(self) -> None:
        if self.property_1st_letter == 'T':
            self.ax.axhline(y = Constants.T_crit, color = '#ffb6c1', linestyle = '-') # horizontal line for T=72, only if plotting T

    def plot_rectangles(self) -> None:
        '''Adds rectangles corresponding to each phase into the plot'''

        rect_transparency = 0.15
        plt.fill_between((rpi.post_milk_flush_time, rpi.prerinse_time),   0, max(self.Y), facecolor= "green", alpha = rect_transparency)
        plt.fill_between((rpi.prerinse_time,        rpi.hot_rinse_time),  0, max(self.Y), facecolor= "blue",  alpha = rect_transparency)
        plt.fill_between((rpi.hot_rinse_time,       rpi.post_rinse_time), 0, max(self.Y), facecolor= "red",   alpha = rect_transparency)

        plt.show() # plots the graph, only use at last function

