"""
fylab.gui.widgets.plot_widget
==============================
Matplotlib-Canvas-Widget für PyQt6.
"""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QTabWidget
from PyQt6.QtCore import Qt


class ScrollableTabWidget(QTabWidget):
    """QTabWidget, das jeden Tab automatisch in eine QScrollArea einbettet.

    Dadurch muss kein Widget individuell mit einer ScrollArea umhüllt werden –
    alle Tabs scrollen automatisch, sobald der Inhalt die sichtbare Fläche übersteigt.
    """

    def addTab(self, widget: QWidget, label: str) -> int:  # type: ignore[override]
        sa = QScrollArea()
        sa.setWidget(widget)
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return super().addTab(sa, label)


class PlotWidget(QWidget):
    """Einbettung einer Matplotlib-Figure in PyQt6."""

    def __init__(self, figure: Figure | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fig = figure or Figure(figsize=(6, 4))
        self._canvas = FigureCanvas(self._fig)
        self._toolbar = NavigationToolbar(self._canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

    def set_figure(self, fig: Figure) -> None:
        """Ersetzt die aktuelle Figure."""
        import matplotlib.pyplot as plt
        plt.close(self._fig)
        self._fig = fig
        self._canvas.figure = fig
        fig.set_canvas(self._canvas)
        # Mindesthöhe setzen, damit QScrollArea einen Scrollbalken anzeigt,
        # wenn die Figurengröße die verfügbare Höhe überschreitet.
        _, h_in = fig.get_size_inches()
        self._canvas.setMinimumHeight(int(h_in * fig.get_dpi()))
        self.updateGeometry()
        self._canvas.draw()

    def refresh(self) -> None:
        self._canvas.draw()
