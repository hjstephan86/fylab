"""
Pytest-Konfiguration für FyLab-Tests.
Setzt Qt auf den Offscreen-Renderer und matplotlib auf den nicht-interaktiven
Agg-Backend, damit GUI-Tests auch in headless Umgebungen (CI, Server)
zuverlässig und ohne Ressource-Warnungen laufen.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
# Verhindert "More than 20 figures opened"-RuntimeWarning über alle Tests.
# Die Figures werden durch den autouse-Fixture nach jedem Test geschlossen.
matplotlib.rcParams["figure.max_open_warning"] = 0

import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def close_all_figures():
    """Schließt nach jedem Test alle offenen Matplotlib-Figures."""
    yield
    plt.close("all")
