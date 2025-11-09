export const StockType = {
  code: String,
  name: String,
  industry: String,
  close: Number,
  change_percent: Number,
  volume: Number,
  date: String,
}

export const TechnicalAnalysisType = {
  name: String,
  type: String,
  parameters: Object,
  description: String,
  created_at: String,
}

export const TradingStrategyType = {
  name: String,
  description: String,
  conditions: Array,
  operation: String,
  is_active: Boolean,
}

export const StockCollectionType = {
  code: String,
  name: String,
  strategy_name: String,
  operation: String,
  price: Number,
  share_amount: Number,
  income: Number,
  signal_date: String,
  created_at: String,
}

export const TradingRecordType = {
  date: String,
  time: String,
  account: String,
  code: String,
  name: String,
  type: String,
  price: Number,
  amount: Number,
  total_value: Number,
  profit: Number,
  reason: String,
  plan: String,
}

export const ConfigurationType = {
  category: String,
  sub_category: String,
  key: String,
  value: String,
  description: String,
}
