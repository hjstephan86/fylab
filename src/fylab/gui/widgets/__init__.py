"""fylab.gui.widgets"""
from fylab.gui.widgets.plot_widget import PlotWidget, ScrollableTabWidget
from fylab.gui.widgets.account_widget import AccountWidget
from fylab.gui.widgets.portfolio_widget import PortfolioWidget
from fylab.gui.widgets.cashflow_widget import CashflowWidget
from fylab.gui.widgets.graph_widget import GraphWidget
from fylab.gui.widgets.risk_widget import RiskWidget

__all__ = [
    "PlotWidget", "ScrollableTabWidget",
    "AccountWidget", "PortfolioWidget",
    "CashflowWidget", "GraphWidget", "RiskWidget",
]
