export interface Stock {
  _id?: string;
  code: string;
  code_name: string;
  tradeStatus: string;
  ipoDate: string;
  outDate: string;
  type: string;
  updateTime: string;
}

export interface StockDailyData {
  _id?: string;
  code: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  preclose: number;
  volume: number;
  amount: number;
  adjustflag: string;
  turn: number;
  tradestatus: number;
  pctChg: number;
  peTTM: number;
  pbMRQ: number;
  psTTM: number;
  pcfNcfTTM: number;
  isST: number;
}

export interface TechnicalIndicator {
  _id?: string;
  code: string;
  date: string;
  cci: number;
  cci_period: number;
  cci_constant: number;
  updated_at: string;
}

export interface TradingStrategy {
  _id?: string;
  name: string;
  conditions: TradingCondition[];
  operation: string;
  is_active: boolean;
  created_at: string;
}

export interface TradingCondition {
  indicator: string;
  operator: string;
  value: number;
  days_ago: number;
}

export interface StockCollection {
  _id?: string;
  code: string;
  code_name?: string;
  strategy_id: string;
  strategy_name: string;
  operation: string;
  price: number;
  share_amount: number;
  meet_date: string;
  added_date: string;
  current_price?: number;
  income?: number;
}

export interface Configuration {
  _id?: string;
  category: string;
  sub_category: string;
  key: string;
  value: string;
  description: string;
  updated_at: string;
}

export interface TradingRecord {
  _id?: string;
  account: string;
  code: string;
  date: string;
  time: string;
  amount: number;
  price: number;
  type: 'buy' | 'sell';
  reason: string;
  trading_plan: string;
  profit?: number;
}
