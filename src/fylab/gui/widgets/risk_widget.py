"""
fylab.gui.widgets.risk_widget
==============================
Risiko-Analyse-Widget: VaR, CVaR, Monte-Carlo-Simulation.
"""

from __future__ import annotations

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QDoubleSpinBox, QSpinBox, QGroupBox,
)

from fylab.analysis.risk import compute_risk_metrics, monte_carlo_portfolio
from fylab.visualization.graph_viz import plot_risk_monte_carlo
from fylab.gui.widgets.plot_widget import PlotWidget, ScrollableTabWidget


class RiskWidget(QWidget):
    """Risikoanalyse: Historical VaR/CVaR + Monte-Carlo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        tabs = ScrollableTabWidget()
        layout.addWidget(tabs)

        # --- Tab 1: Risikokennzahlen ---
        tab_metrics = QWidget()
        ml = QVBoxLayout(tab_metrics)

        info = QLabel(
            "Berechnet historischen <b>Value-at-Risk (VaR)</b>, "
            "<b>Conditional VaR (CVaR/Expected Shortfall)</b>, "
            "Max-Drawdown und Sharpe-Ratio auf Basis simulierter Renditen."
        )
        info.setWordWrap(True)
        ml.addWidget(info)

        # Parameter
        param_box = QGroupBox("Parameter")
        param_form = QFormLayout(param_box)
        self._ret_mean = QDoubleSpinBox()
        self._ret_mean.setRange(-0.5, 0.5)
        self._ret_mean.setValue(0.08)
        self._ret_mean.setSuffix(" p.a.")
        self._ret_vol = QDoubleSpinBox()
        self._ret_vol.setRange(0.01, 1.0)
        self._ret_vol.setValue(0.20)
        self._ret_vol.setSuffix(" p.a.")
        self._risk_free = QDoubleSpinBox()
        self._risk_free.setRange(0.0, 0.2)
        self._risk_free.setValue(0.03)
        self._risk_free.setSuffix(" p.a.")
        param_form.addRow("Erwartete Rendite:", self._ret_mean)
        param_form.addRow("Volatilität:", self._ret_vol)
        param_form.addRow("Risikofreier Zins:", self._risk_free)
        ml.addWidget(param_box)

        btn_calc = QPushButton("Risikokennzahlen berechnen")
        btn_calc.clicked.connect(self._calc_metrics)
        ml.addWidget(btn_calc)

        self._metrics_widget = QGroupBox("Ergebnisse")
        metrics_layout = QFormLayout(self._metrics_widget)
        self._lbl_var95 = QLabel("–")
        self._lbl_var99 = QLabel("–")
        self._lbl_cvar95 = QLabel("–")
        self._lbl_maxdd = QLabel("–")
        self._lbl_vol = QLabel("–")
        self._lbl_sharpe = QLabel("–")
        metrics_layout.addRow("VaR (95%):", self._lbl_var95)
        metrics_layout.addRow("VaR (99%):", self._lbl_var99)
        metrics_layout.addRow("CVaR (95%):", self._lbl_cvar95)
        metrics_layout.addRow("Max. Drawdown:", self._lbl_maxdd)
        metrics_layout.addRow("Volatilität (p.a.):", self._lbl_vol)
        metrics_layout.addRow("Sharpe-Ratio:", self._lbl_sharpe)
        ml.addWidget(self._metrics_widget)
        tabs.addTab(tab_metrics, "VaR / CVaR")

        # --- Tab 2: Monte-Carlo ---
        tab_mc = QWidget()
        cl = QVBoxLayout(tab_mc)

        mc_info = QLabel(
            "<b>Monte-Carlo-Simulation</b>: Simuliert n Portfoliopfade über 252 "
            "Handelstage (1 Jahr) basierend auf normalverteilten täglichen Renditen."
        )
        mc_info.setWordWrap(True)
        cl.addWidget(mc_info)

        mc_params = QGroupBox("Parameter")
        mcp_form = QFormLayout(mc_params)
        self._n_sim = QSpinBox()
        self._n_sim.setRange(100, 50000)
        self._n_sim.setValue(10000)
        self._n_sim.setSingleStep(1000)
        self._initial_val = QDoubleSpinBox()
        self._initial_val.setRange(1000, 10_000_000)
        self._initial_val.setValue(100_000)
        self._initial_val.setSuffix(" €")
        self._initial_val.setSingleStep(10000)
        mcp_form.addRow("Simulationen:", self._n_sim)
        mcp_form.addRow("Startwert:", self._initial_val)
        cl.addWidget(mc_params)

        btn_mc = QPushButton("Monte-Carlo starten")
        btn_mc.clicked.connect(self._run_monte_carlo)
        cl.addWidget(btn_mc)

        self._plot_mc = PlotWidget()
        cl.addWidget(self._plot_mc)
        tabs.addTab(tab_mc, "Monte-Carlo")

    def _calc_metrics(self) -> None:
        mu = self._ret_mean.value() / 252
        sigma = self._ret_vol.value() / np.sqrt(252)
        rf = self._risk_free.value()
        rng = np.random.default_rng(42)
        returns = rng.normal(mu, sigma, 2520)   # 10 Jahre tägliche Renditen
        metrics = compute_risk_metrics(returns, rf)

        def fmt(val: float) -> str:
            return f"{val:.2%}"

        self._lbl_var95.setText(fmt(metrics.var_95))
        self._lbl_var99.setText(fmt(metrics.var_99))
        self._lbl_cvar95.setText(fmt(metrics.cvar_95))
        self._lbl_maxdd.setText(fmt(metrics.max_drawdown))
        self._lbl_vol.setText(fmt(metrics.volatility_annual))
        color = "#27ae60" if metrics.sharpe_ratio >= 1 else "#e74c3c"
        self._lbl_sharpe.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._lbl_sharpe.setText(f"{metrics.sharpe_ratio:.2f}")

    def _run_monte_carlo(self) -> None:
        mu = self._ret_mean.value()
        sigma = self._ret_vol.value()
        n = self._n_sim.value()
        v0 = self._initial_val.value()
        weights = np.array([1.0])
        mean_returns = np.array([mu])
        cov = np.array([[sigma ** 2]])
        sims = monte_carlo_portfolio(weights, mean_returns, cov,
                                     n_simulations=n, initial_value=v0)
        fig = plot_risk_monte_carlo(
            sims, f"Monte-Carlo ({n:,} Simulationen, Start: {v0:,.0f} €)"
        )
        self._plot_mc.set_figure(fig)
