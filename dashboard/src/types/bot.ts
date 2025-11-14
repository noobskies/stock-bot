import type { TradingMode } from "./trading";

export interface BotStatus {
  is_running: boolean;
  mode: TradingMode;
  is_paper_trading: boolean;
  uptime: number;
  last_cycle: string | null;
  market_open: boolean;
}

export interface BotSettings {
  trading: {
    mode: TradingMode;
    symbols: string[];
    close_positions_eod: boolean;
  };
  risk: {
    risk_per_trade: number;
    max_position_size: number;
    max_portfolio_exposure: number;
    daily_loss_limit: number;
    stop_loss_percent: number;
    trailing_stop_percent: number;
    trailing_stop_activation: number;
  };
  ml: {
    model_path: string;
    sequence_length: number;
    prediction_confidence_threshold: number;
    auto_execute_threshold: number;
    retrain_frequency: string;
  };
  is_paper_trading: boolean;
}
