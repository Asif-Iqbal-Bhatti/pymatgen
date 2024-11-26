"""This module defines generic plotters."""

from __future__ import annotations

import importlib

import matplotlib.pyplot as plt

from pymatgen.util.plotting import pretty_plot


class SpectrumPlotter:
    """Plot Spectrum objects and subclasses.

    Note that the interface is extremely flexible given that there are many
    different ways in which people want to view spectra. The typical usage is:

        # Initializes plotter with some optional args. Defaults are usually
        # fine,
        plotter = SpectrumPlotter()

        # Adds a DOS (A kind of spectra) with a label.
        plotter.add_spectrum("Total DOS", dos)

        # Alternatively, you can add a dict of DOSs. This is the typical
        # form returned by CompleteDos.get_spd/element/others_dos().
        plotter.add_spectra({"dos1": dos1, "dos2": dos2})
    """

    def __init__(self, xshift=0.0, yshift=0.0, stack=False, color_cycle=("qualitative", "Set1_9")):
        """
        Args:
            xshift (float): A shift that is applied to the x values. This is
                commonly used to shift to an arbitrary zero. e.g. zeroing at the
                Fermi energy in DOS, or at the absorption edge in XAS spectra. The
                same xshift is applied to all spectra.
            yshift (float): A shift that is applied to the y values. This is
                commonly used to displace spectra for easier visualization.
                Successive spectra are applied successive shifts.
            stack (bool): Whether to stack plots rather than simply plot them.
                For example, DOS plot can usually be stacked to look at the
                contribution of each orbital.
            color_cycle (str): Default color cycle to use. Note that this can be
                overridden.
        """
        self.xshift = xshift
        self.yshift = yshift
        self.stack = stack

        mod = importlib.import_module(f"palettable.colorbrewer.{color_cycle[0]}")
        self.colors_cycle = getattr(mod, color_cycle[1]).mpl_colors
        self.colors: list = []
        self._spectra: dict = {}

    def add_spectrum(self, label, spectrum, color=None):
        """
        Adds a Spectrum for plotting.

        Args:
            label (str): Label for the Spectrum. Must be unique.
            spectrum: Spectrum object
            color (str): This is passed on to matplotlib. e.g. "k--" indicates
                a dashed black line. If None, a color will be chosen based on
                the default color cycle.
        """
        for attribute in "xy":
            if not hasattr(spectrum, attribute):
                raise ValueError(f"spectrum of type={type(spectrum)} missing required {attribute=}")
        self._spectra[label] = spectrum
        self.colors.append(color or self.colors_cycle[len(self._spectra) % len(self.colors_cycle)])

    def add_spectra(self, spectra_dict, key_sort_func=None):
        """
        Add a dictionary of Spectrum, with an optional sorting function for the
        keys.

        Args:
            spectra_dict: dict of {label: Spectrum}
            key_sort_func: function used to sort the dos_dict keys.
        """
        keys = sorted(spectra_dict, key=key_sort_func) if key_sort_func else list(spectra_dict)
        for label in keys:
            self.add_spectrum(label, spectra_dict[label])

    def get_plot(self, xlim=None, ylim=None):
        """Get a matplotlib plot showing the DOS.

        Args:
            xlim: Specifies the x-axis limits. Set to None for automatic
                determination.
            ylim: Specifies the y-axis limits.
        """
        ax = pretty_plot(12, 8)
        base = 0.0
        for idx, (key, sp) in enumerate(self._spectra.items()):
            if not self.stack:
                ax.plot(
                    sp.x,
                    sp.y + self.yshift * idx,
                    color=self.colors[idx],
                    label=str(key),
                    linewidth=3,
                )
            else:
                ax.fill_between(
                    sp.x,
                    base,
                    sp.y + self.yshift * idx,
                    color=self.colors[idx],
                    label=str(key),
                    linewidth=3,
                )
                base = sp.y + base
            ax.set_xlabel(sp.XLABEL)
            ax.set_ylabel(sp.YLABEL)

        if xlim:
            ax.set_xlim(xlim)
        if ylim:
            ax.set_ylim(ylim)

        ax.legend()
        legend_text = ax.get_legend().get_texts()  # all the text.Text instance in the legend
        plt.setp(legend_text, fontsize=30)
        plt.tight_layout()
        return ax

    def save_plot(self, filename: str, **kwargs):
        """Save matplotlib plot to a file.

        Args:
            filename (str): Filename to write to. Must include extension to specify image format.
            kwargs: passed to get_plot.
        """
        self.get_plot(**kwargs)
        plt.savefig(filename)

    def show(self, **kwargs):
        """Show the plot using matplotlib."""
        self.get_plot(**kwargs)
        plt.show()