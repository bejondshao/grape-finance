// 股票数据处理工具函数

// 根据时间周期聚合数据
export const aggregateData = (data, frame) => {
  if (frame === 'daily') {
    return data;
  }

  const aggregated = [];
  const groupedData = {};

  // 按周期分组数据
  data.forEach(item => {
    let key;
    const date = item.date; // 这里是Date对象
    
    switch (frame) {
      case 'weekly':
        // 按周分组 (ISO周)
        const weekYear = date.getFullYear();
        const startOfYear = new Date(weekYear, 0, 1);
        const days = Math.floor((date - startOfYear) / (24 * 60 * 60 * 1000));
        const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7);
        key = `${weekYear}-W${weekNumber}`;
        break;
      case 'monthly':
        // 按月分组
        key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
        break;
      case 'quarterly':
        // 按季度分组
        const quarter = Math.floor(date.getMonth() / 3) + 1;
        key = `${date.getFullYear()}-Q${quarter}`;
        break;
      default:
        key = date.toISOString().split('T')[0];
    }

    if (!groupedData[key]) {
      groupedData[key] = [];
    }
    groupedData[key].push(item);
  });

  // 为每个周期计算聚合数据
  Object.keys(groupedData).forEach(key => {
    const group = groupedData[key];
    if (group.length === 0) return;

    // 按日期排序
    group.sort((a, b) => a.date - b.date);

    const open = group[0].open;
    const close = group[group.length - 1].close;
    const high = Math.max(...group.map(item => item.high));
    const low = Math.min(...group.map(item => item.low));
    const volume = group.reduce((sum, item) => sum + item.volume, 0);
    const amount = group.reduce((sum, item) => sum + item.amount, 0);
    const turn = group.reduce((sum, item) => sum + item.turn, 0) / group.length; // 平均换手率
    
    // 财务指标取最后一个数据点的值
    const peTTM = group[group.length - 1].peTTM;
    const pbMRQ = group[group.length - 1].pbMRQ;
    const psTTM = group[group.length - 1].psTTM;
    const pcfNcfTTM = group[group.length - 1].pcfNcfTTM;
    // CCI指标取周期内最后一个非空值
    let cci = null;
    for (let i = group.length - 1; i >= 0; i--) {
      if (group[i].cci !== null && group[i].cci !== undefined) {
        cci = group[i].cci;
        break;
      }
    }

    // 计算涨跌幅度 (基于周期内第一个交易日的前一天收盘价)
    const preclose = group[0].preclose;
    const change = close - preclose;
    const changePercent = preclose !== 0 ? (change / preclose) * 100 : 0;

    aggregated.push({
      date: group[group.length - 1].date, // 使用周期最后一天的日期
      open,
      close,
      high,
      low,
      volume,
      amount,
      turn,
      peTTM,
      pbMRQ,
      psTTM,
      pcfNcfTTM,
      cci, // CCI指标
      change,        // 涨跌金额
      changePercent  // 涨跌百分比
    });
  });

  // 按日期排序
  return aggregated.sort((a, b) => a.date - b.date);
};

// 根据股票代码确定市场前缀
export const getMarketPrefix = (code) => {
  if (code.startsWith('6') || code.startsWith('8')) {
    return 'sh';
  } else if (code.startsWith('3') || code.startsWith('0') || code.startsWith('1')) {
    return 'sz';
  } else if (code.startsWith('4') || code.startsWith('9')) {
    return 'bj';
  } else {
    return 'sh'; // 默认上海
  }
};

// 标准化股票代码
export const normalizeStockCode = (code) => {
  if (code.indexOf('.') !== -1) {
    return code; // 已经是标准格式
  }
  return `${getMarketPrefix(code)}.${code}`;
};

// 计算移动平均线
export const calculateMA = (data, period) => {
  if (!data || data.length < period) return [];
  
  const result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null); // 前period-1个数据点无法计算MA
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      result.push(sum / period);
    }
  }
  return result;
};