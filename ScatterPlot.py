import numpy as np
from PlotBase import PlotBase

class ScatterPlot(PlotBase):
    def __init__(self, parent, row, col, title, ylim, xlim, resizable=0, xlabel=None, ylabel=None):
        super().__init__(parent, row, col, title, ylim, xlim, resizable, xlabel, ylabel)
        if resizable and not hasattr(self, 'resize_automatic'):
            raise AttributeError('resize_automatic not set for ScatterPlot while resizable non-zero')

        self.scatters = []

    def add_scatter(self, *scatters: tuple[str, str, str, str]) -> None:
        empty = np.empty(self.parent.MAX_READINGS)

        for label, data_x, data_y, colour in scatters:
            scatter = self.ax.scatter(empty, empty, c=colour, s=100, label=label)
            scatter.set_animated(True)

            self.scatters.append({'scatter': scatter, 'data_x': data_x, 'data_y': data_y})

        self.ax.legend(loc='upper left')

    def draw_artists(self, data: dict[str, np.ndarray]) -> None:
        # Update scatters
        for scatter_data in self.scatters:
            scatter_data['scatter'].set_offsets(
                np.column_stack((data[scatter_data['data_x']], data[scatter_data['data_y']]))
            )
            self.ax.draw_artist(scatter_data['scatter'])

    def resize_automatic(self, data: dict[str, np.ndarray]) -> None:

        all_values = np.concatenate([data[scatter['data_x']] for scatter in self.scatters])
        min_val, max_val = np.nanmin(all_values), np.nanmax(all_values)

        range_vals = abs(max_val - min_val) or 1

        desired_min = min_val - range_vals * 0.2
        desired_max = max_val + range_vals * 0.2
        threshold = range_vals * self.resizable

        if abs(desired_min - self.xlim[0]) > threshold or abs(desired_max - self.xlim[1]) > threshold:
            self.background_needs_cache = True
            self.xlim = [desired_min, desired_max]

        all_values = np.concatenate([data[scatter['data_y']] for scatter in self.scatters])
        min_val, max_val = np.nanmin(all_values), np.nanmax(all_values)

        range_vals = abs(max_val - min_val) or 1

        desired_min = min_val - range_vals * self.resizable * 0.75
        desired_max = max_val + range_vals * self.resizable * 0.75
        threshold = range_vals * self.resizable

        if abs(desired_min - self.ylim[0]) > threshold or abs(desired_max - self.ylim[1]) > threshold:
            self.background_needs_cache = True
            self.ylim = [desired_min, desired_max]