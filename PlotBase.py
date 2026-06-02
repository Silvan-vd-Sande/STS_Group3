from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotBase:
    def __init__(self, parent, row, col, title, ylim, xlim, resizable, xlabel, ylabel):
        self.parent = parent

        self.ylim = ylim
        self.xlim = xlim
        self.scatters = []
        self.resizable = resizable

        self.fig = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent.plot_frame)

        self.canvas.get_tk_widget().grid(
            row=row,
            column=col,
            sticky="nsew",
            padx=5,
            pady=5
        )

        self.fig.subplots_adjust(left=0.2)

        self.bg = None

        self.ax.ticklabel_format(style='sci', axis='both', scilimits=(0, 0))

        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(*ylim)

        if xlabel is not None:
            self.ax.set_xlabel(xlabel)
        if ylabel is not None:
            self.ax.set_ylabel(ylabel)

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title(title)


        self.canvas.draw_idle()

        self.background_needs_cache = True

    def draw_plot(self, data):
        if self.background_needs_cache:
            # Update limits if needed
            self.ax.set_ylim(*self.ylim)
            self.ax.set_xlim(*self.xlim)

            # Draw and cache new background
            self.canvas.draw()
            self.bg = self.canvas.copy_from_bbox(self.ax.bbox)

            self.background_needs_cache = False

        # Restore only this axes
        self.canvas.restore_region(self.bg)

        self.draw_artists(data)

        # Blit only this axes
        self.canvas.blit(self.ax.bbox)

    def draw_artists(self, data):
        # Defined by the plot type
        return

    def destroy(self):
        """Clean up the plot."""
        self.canvas.get_tk_widget().destroy()