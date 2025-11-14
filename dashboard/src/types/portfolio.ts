export interface PortfolioData {
  total_value: number;
  cash: number;
  positions_value: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  buying_power: number;
}

export interface RiskMetrics {
  total_exposure: number;
  position_count: number;
  max_positions: number;
  daily_loss_limit: number;
  circuit_breaker_active: boolean;
}

export interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  market_value: number;
  stop_loss: number | null;
  trailing_stop: number | null;
}

export interface PerformanceMetrics {
  win_rate: number;
  total_trades: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface PortfolioResponse {
  portfolio: PortfolioData;
  risk: RiskMetrics;
  positions: Position[];
  performance: PerformanceMetrics;
}
