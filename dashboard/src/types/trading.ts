export type TradingMode = "auto" | "manual" | "hybrid";
export type SignalType = "BUY" | "SELL" | "LONG" | "SHORT";
export type SignalStatus = "pending" | "approved" | "rejected" | "executed";
export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit";
export type TimeInForce = "day" | "gtc" | "ioc" | "fok";

export interface TradingSignal {
  id: number;
  symbol: string;
  signal_type: SignalType;
  confidence: number;
  predicted_direction: string;
  entry_price: number;
  suggested_quantity: number;
  features: string;
  timestamp: string;
}

export interface Trade {
  id: number;
  symbol: string;
  action: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  pnl: number;
  pnl_percent: number;
  status: string;
  entry_time: string;
  exit_time: string | null;
  stop_loss: number | null;
  confidence: number | null;
}

export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  limit_price: number | null;
  stop_price: number | null;
  time_in_force: TimeInForce;
  submitted_at: string;
}

export interface PlaceOrderRequest {
  symbol: string;
  side: OrderSide;
  quantity: number;
  type: OrderType;
  limit_price?: number;
  time_in_force?: TimeInForce;
}

export interface TradeFilters {
  symbol?: string;
  days?: number;
  status?: string;
  side?: string;
  startDate?: string;
  endDate?: string;
  include_archived?: boolean;
}
