import numpy as np
from PlotBase import PlotBase


class LinePlot(PlotBase):
    def __init__(self, parent, row, col, title, ylim, xlim=(-5, 0), resizable=0, xlabel=None, ylabel=None):
        super().__init__(parent, row, col, title, ylim, xlim, resizable, xlabel, ylabel)
        if resizable and not hasattr(self, 'resize_automatic'):
            raise AttributeError('resize_automatic not set for LinePlot while resizable non-zero')
        self.ax.ticklabel_format(style='sci')
        self.lines = []

    def add_lines(self, *lines):
        for label, data, colour in lines:
            line, = self.ax.plot([], [], linestyle='-', linewidth=2,
                            color=colour, label=label)
            line.set_animated(True)
            self.lines.append({'line': line, 'data': data})
        self.ax.legend(loc='upper left')

    def draw_artists(self, data):
        # Update lines
        for line_data in self.lines:
            line_data['line'].set_data(data['time'], data[line_data['data']])

            self.ax.draw_artist(line_data['line'])

    def resize_automatic(self, data):
        all_values = np.concatenate([data[line['data']] for line in self.lines])
        min_val, max_val = float(np.nanmin(all_values)), float(np.nanmax(all_values))

        range_vals = abs(max_val - min_val) or 1

        threshold = range_vals * self.resizable
        desired_min = min_val - threshold
        desired_max = max_val + threshold

        if abs(desired_min - self.ylim[0]) > threshold or abs(desired_max - self.ylim[1]) > threshold:
            self.background_needs_cache = True
            self.ylim = [desired_min, desired_max]
