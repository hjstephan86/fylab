"""fylab.algorithms"""
from fylab.algorithms.subgraph_finance import (
    FraudPattern, FraudDetectionResult, AdjGraph,
    build_transaction_graph, detect_fraud_patterns, subgraph_contains,
)
from fylab.algorithms.mst import (
    MSTResult, compute_portfolio_mst,
    PortfolioStructureComparison, compare_portfolio_structures,
)
from fylab.algorithms.max_flow import (
    FlowResult, DebtTransaction, compute_max_flow, simplify_debts,
    DebtPattern, DebtPatternResult, detect_debt_patterns,
)
from fylab.algorithms.arbitrage import (
    ArbitrageResult, detect_arbitrage,
    CyclePattern, CyclePatternResult, detect_cycle_patterns,
)

__all__ = [
    # subgraph_finance
    "FraudPattern", "FraudDetectionResult", "AdjGraph",
    "build_transaction_graph", "detect_fraud_patterns", "subgraph_contains",
    # mst
    "MSTResult", "compute_portfolio_mst",
    "PortfolioStructureComparison", "compare_portfolio_structures",
    # max_flow
    "FlowResult", "DebtTransaction", "compute_max_flow", "simplify_debts",
    "DebtPattern", "DebtPatternResult", "detect_debt_patterns",
    # arbitrage
    "ArbitrageResult", "detect_arbitrage",
    "CyclePattern", "CyclePatternResult", "detect_cycle_patterns",
]
