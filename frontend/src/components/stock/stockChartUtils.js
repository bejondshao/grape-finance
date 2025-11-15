// 股票图表绘制工具函数
import { calculateMA } from './stockDataUtils';

// 绘制K线图上的CCI信号箭头
export const drawCCISignalsOnKLine = (ctx, cciPoints, margin) => {
  // 遍历CCI点，检测交叉信号
  for (let i = 1; i < cciPoints.length; i++) {
    const prevPoint = cciPoints[i - 1];
    const currPoint = cciPoints[i];
    
    // 检查CCI上穿-100（从下往上穿过-100线）
    if (prevPoint.cci <= -100 && currPoint.cci > -100) {
      // 在K线下方绘制红色上箭头（买入信号）
      drawSignalArrow(ctx, currPoint.x, currPoint.yLow + 20, 'up', '#ff0000'); // 红色上箭头
    }
    
    // 检查CCI下穿100（从上往下穿过100线）
    if (prevPoint.cci >= 100 && currPoint.cci < 100) {
      // 在K线上方绘制绿色下箭头（卖出信号）
      drawSignalArrow(ctx, currPoint.x, currPoint.yHigh - 20, 'down', '#00ff00'); // 绿色下箭头
    }
  }
};

// 绘制CCI信号箭头
export const drawCCISignals = (ctx, cciPoints, yCci100, yCciMinus100, margin) => {
  // 遍历CCI点，检测交叉信号
  for (let i = 1; i < cciPoints.length; i++) {
    const prevPoint = cciPoints[i - 1];
    const currPoint = cciPoints[i];
    
    // 检查CCI上穿-100（从下往上穿过-100线）
    if (prevPoint.cci <= -100 && currPoint.cci > -100) {
      drawSignalArrow(ctx, currPoint.x, yCciMinus100, 'up', '#ff0000'); // 红色上箭头
    }
    
    // 检查CCI下穿100（从上往下穿过100线）
    if (prevPoint.cci >= 100 && currPoint.cci < 100) {
      drawSignalArrow(ctx, currPoint.x, yCci100, 'down', '#00ff00'); // 绿色下箭头
    }
  }
};

// 绘制信号箭头
export const drawSignalArrow = (ctx, x, y, direction, color) => {
  const arrowSize = 8; // 缩小箭头尺寸
  
  ctx.fillStyle = color;
  
  if (direction === 'up') {
    // 绘制向上的箭头
    ctx.beginPath();
    ctx.moveTo(x, y - arrowSize); // 箭头顶部
    ctx.lineTo(x - arrowSize/2, y); // 左下角
    ctx.lineTo(x + arrowSize/2, y); // 右下角
    ctx.closePath();
    ctx.fill();
  } else if (direction === 'down') {
    // 绘制向下的箭头
    ctx.beginPath();
    ctx.moveTo(x, y + arrowSize); // 箭头底部
    ctx.lineTo(x - arrowSize/2, y); // 左上角
    ctx.lineTo(x + arrowSize/2, y); // 右上角
    ctx.closePath();
    ctx.fill();
  }
};

// 绘制完整的股票图表
export const drawStockChart = (canvas, chartContainerRef, stockData, technicalData, selectedCode, stockName, zoomRange, hoverInfo, timeFrame, maSettings) => {
  if (!stockData.length || !chartContainerRef.current) return;

  const drawChart = () => {
    const container = chartContainerRef.current;
    const width = container.clientWidth;
    const height = 800; // 增加高度以容纳CCI图表和KDJ图表
    
    // 清空容器
    container.innerHTML = '';
    
    // 创建canvas元素
    const canvasElement = document.createElement('canvas');
    canvasElement.width = width;
    canvasElement.height = height;
    canvasElement.style.display = 'block';
    canvasElement.style.cursor = 'default';
    container.appendChild(canvasElement);
    
    // 保存canvas引用
    const ctx = canvasElement.getContext('2d');
    
    // 设置图表参数
    const margin = { top: 20, right: 50, bottom: 50, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // K线图区域高度 (35%)
    const kLineHeight = chartHeight * 0.35;
    // 图表间间距 (2%)
    const gap = chartHeight * 0.02;
    // 交易量图区域高度 (20%)
    const volumeHeight = chartHeight * 0.20;
    // CCI图表区域高度 (20%)
    const cciHeight = chartHeight * 0.20;
    // KDJ图表区域高度 (20%)
    const kdjHeight = chartHeight * 0.20;
    
    // 获取当前显示的数据
    const visibleData = stockData.slice(zoomRange.start, zoomRange.end + 1);
    if (visibleData.length === 0) return;
    
    // 计算价格范围
    const prices = visibleData.flatMap(d => [d.high, d.low]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1; // 防止除零错误
    
    // 计算交易量范围
    const volumes = visibleData.map(d => d.volume);
    const maxVolume = Math.max(...volumes) || 1; // 防止除零错误
    
    // 计算成交额范围（用于颜色深浅）
    const amounts = visibleData.map(d => d.amount);
    const maxAmount = Math.max(...amounts) || 1;
    
    // 计算CCI范围（过滤掉null值）
    const cciValues = visibleData
      .map(d => d.cci)
      .filter(cci => cci !== null && cci !== undefined && !isNaN(cci));

    let minCci = -150;  // 默认最小值
    let maxCci = 150;   // 默认最大值
    
    if (cciValues.length > 0) {
      const actualMinCci = Math.min(...cciValues);
      const actualMaxCci = Math.max(...cciValues);
      // 确保范围比100和-100更大
      minCci = Math.min(actualMinCci, -150);
      maxCci = Math.max(actualMaxCci, 150);
    }
    
    const cciRange = maxCci - minCci || 1;
    
    // 计算KDJ范围
    const kValues = visibleData
      .map(d => d.kdj_k)
      .filter(k => k !== null && k !== undefined && !isNaN(k));
      
    const dValues = visibleData
      .map(d => d.kdj_d)
      .filter(d => d !== null && d !== undefined && !isNaN(d));
      
    const jValues = visibleData
      .map(d => d.kdj_j)
      .filter(j => j !== null && j !== undefined && !isNaN(j));
    
    let minKdj = 0;   // KDJ默认最小值
    let maxKdj = 100; // KDJ默认最大值
    
    if (kValues.length > 0 || dValues.length > 0 || jValues.length > 0) {
      const allKdjValues = [...kValues, ...dValues, ...jValues];
      if (allKdjValues.length > 0) {
        const actualMinKdj = Math.min(...allKdjValues);
        const actualMaxKdj = Math.max(...allKdjValues);
        // 确保范围包含0-100，但也要考虑实际数据范围
        minKdj = Math.min(actualMinKdj, 0);
        maxKdj = Math.max(actualMaxKdj, 100);
      }
    }
    
    const kdjRange = maxKdj - minKdj || 1;

    // 绘制背景网格
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;
    
    // 垂直网格线
    const pointsCount = visibleData.length;
    for (let i = 0; i <= 10; i++) {
      const x = margin.left + (i * chartWidth / 10);
      ctx.beginPath();
      ctx.moveTo(x, margin.top);
      ctx.lineTo(x, margin.top + kLineHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap + volumeHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + kdjHeight);
      ctx.stroke();
    }
    
    // 水平网格线 - K线图区域
    for (let i = 0; i <= 5; i++) {
      const y = margin.top + (i * kLineHeight / 5);
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + chartWidth, y);
      ctx.stroke();
    }
    
    // 水平网格线 - 交易量图区域
    for (let i = 0; i <= 3; i++) {
      const y = margin.top + kLineHeight + gap + (i * volumeHeight / 3);
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + chartWidth, y);
      ctx.stroke();
    }
    
    // 水平网格线 - CCI图区域
    for (let i = 0; i <= 3; i++) {
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + (i * cciHeight / 3);
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + chartWidth, y);
      ctx.stroke();
    }
    
    // 水平网格线 - KDJ图区域
    for (let i = 0; i <= 4; i++) {
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + (i * kdjHeight / 4);
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + chartWidth, y);
      ctx.stroke();
    }
    
    // 绘制坐标轴
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    
    // Y轴 - 价格轴
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top);
    ctx.lineTo(margin.left, margin.top + kLineHeight);
    ctx.stroke();
    // 右侧Y轴 - 价格轴
    ctx.beginPath();
    ctx.moveTo(margin.left + chartWidth, margin.top);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight);
    ctx.stroke();
    
    // Y轴 - 交易量轴
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight + gap);
    ctx.lineTo(margin.left, margin.top + kLineHeight + gap + volumeHeight);
    ctx.stroke();
    // 右侧Y轴 - 交易量轴
    ctx.beginPath();
    ctx.moveTo(margin.left + chartWidth, margin.top + kLineHeight + gap);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight);
    ctx.stroke();
    
    // Y轴 - CCI轴
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap);
    ctx.lineTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
    ctx.stroke();
    // 右侧Y轴 - CCI轴
    ctx.beginPath();
    ctx.moveTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight + gap);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
    ctx.stroke();
    
    // Y轴 - KDJ轴
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap);
    ctx.lineTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + kdjHeight);
    ctx.stroke();
    // 右侧Y轴 - KDJ轴
    ctx.beginPath();
    ctx.moveTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + kdjHeight);
    ctx.stroke();
    
    // X轴
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight + gap + volumeHeight);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
    ctx.lineTo(margin.left + chartWidth, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
    ctx.stroke();
    
    // 绘制Y轴标签 - 价格
    ctx.fillStyle = '#000';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const price = maxPrice - (i * priceRange / 5);
      const y = margin.top + (i * kLineHeight / 5);
      ctx.fillText(price.toFixed(2), margin.left - 5, y + 4);
      // 右侧Y轴标签 - 价格
      ctx.textAlign = 'left';
      ctx.fillText(price.toFixed(2), margin.left + chartWidth + 5, y + 4);
    }
    
    // 绘制Y轴标签 - 交易量
    for (let i = 0; i <= 3; i++) {
      const volume = maxVolume - (i * maxVolume / 3);
      const y = margin.top + kLineHeight + gap + (i * volumeHeight / 3);
      const volumeInMillions = volume / 1000000;
      ctx.fillText(volumeInMillions >= 1 ? volumeInMillions.toFixed(1) + 'M' : volume.toFixed(0), margin.left - 5, y + 4);
      // 右侧Y轴标签 - 交易量
      ctx.textAlign = 'left';
      ctx.fillText(volumeInMillions >= 1 ? volumeInMillions.toFixed(1) + 'M' : volume.toFixed(0), margin.left + chartWidth + 5, y + 4);
    }
    
    // 绘制Y轴标签 - CCI
    for (let i = 0; i <= 3; i++) {
      const cciValue = maxCci - (i * cciRange / 3);
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + (i * cciHeight / 3);
      ctx.fillText(cciValue.toFixed(0), margin.left - 5, y + 4);
      // 右侧Y轴标签 - CCI
      ctx.textAlign = 'left';
      ctx.fillText(cciValue.toFixed(0), margin.left + chartWidth + 5, y + 4);
    }
    
    // 绘制Y轴标签 - KDJ
    for (let i = 0; i <= 4; i++) {
      const kdjValue = maxKdj - (i * kdjRange / 4);
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + (i * kdjHeight / 4);
      ctx.fillText(kdjValue.toFixed(0), margin.left - 5, y + 4);
      // 右侧Y轴标签 - KDJ
      ctx.textAlign = 'left';
      ctx.fillText(kdjValue.toFixed(0), margin.left + chartWidth + 5, y + 4);
    }
    
    // 恢复文本对齐方式
    ctx.textAlign = 'right';
    
    // 绘制X轴标签
    ctx.textAlign = 'center';
    const step = Math.max(1, Math.floor(pointsCount / 10));
    for (let i = 0; i < pointsCount; i += step) {
      const actualIndex = zoomRange.start + i;
      if (actualIndex < stockData.length) {
        const x = margin.left + (i * chartWidth / (pointsCount - 1));
        const date = stockData[actualIndex].date; // 这里是Date对象
        
        // 根据时间周期显示不同的日期格式
        let label;
        switch (timeFrame) {
          case 'weekly':
            label = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
            break;
          case 'monthly':
            label = `${date.getFullYear()}-${date.getMonth() + 1}`;
            break;
          case 'quarterly':
            const quarter = Math.floor(date.getMonth() / 3) + 1;
            label = `${date.getFullYear()}Q${quarter}`;
            break;
          default:
            label = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
        }
        
        const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + kdjHeight + 15;
        ctx.fillText(label, x, y);
      }
    }
    
    // 绘制K线
    const barWidth = Math.max(1, chartWidth / pointsCount - 1);
    const kLineCCIPoints = []; // 用于存储CCI点，以便在K线图上绘制信号箭头
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      
      // 计算Y坐标
      const yOpen = margin.top + ((maxPrice - point.open) / priceRange) * kLineHeight;
      const yClose = margin.top + ((maxPrice - point.close) / priceRange) * kLineHeight;
      const yHigh = margin.top + ((maxPrice - point.high) / priceRange) * kLineHeight;
      const yLow = margin.top + ((maxPrice - point.low) / priceRange) * kLineHeight;
      
      // 设置颜色 (根据涨跌)
      const isUp = point.close >= point.open;
      ctx.strokeStyle = isUp ? '#ef5350' : '#66bb6a';
      ctx.fillStyle = isUp ? '#ef5350' : '#66bb6a';
      
      // 绘制影线
      ctx.beginPath();
      ctx.moveTo(x, yHigh);
      ctx.lineTo(x, yLow);
      ctx.stroke();
      
      // 绘制实体
      const rectHeight = Math.abs(yOpen - yClose);
      const rectY = Math.min(yOpen, yClose);
      if (rectHeight > 0) {
        ctx.fillRect(x - barWidth/2, rectY, barWidth, Math.max(1, rectHeight));
      } else {
        ctx.beginPath();
        ctx.moveTo(x - barWidth/2, rectY);
        ctx.lineTo(x + barWidth/2, rectY);
        ctx.stroke();
      }
      
      // 收集CCI点信息用于在K线图上绘制信号箭头
      if (point.cci !== null && point.cci !== undefined && !isNaN(point.cci)) {
        kLineCCIPoints.push({ 
          x, 
          cci: point.cci, 
          index: i,
          yHigh,
          yLow
        });
      }
    }
    
    // 在K线图上绘制CCI信号箭头
    drawCCISignalsOnKLine(ctx, kLineCCIPoints, margin);
    
    // 绘制均线
    const maColors = {
      ma5: '#ff0000',   // 红色
      ma10: '#00ff00',  // 绿色
      ma15: '#0000ff',  // 蓝色
      ma20: '#ffa500',  // 橙色（加深20日均线颜色）
      ma30: '#ff00ff',  // 紫色
      ma60: '#00ffff',  // 青色
      ma120: '#ffa500'  // 橙色
    };
    
    const maPeriods = {
      ma5: 5,
      ma10: 10,
      ma15: 15,
      ma20: 20,
      ma30: 30,
      ma60: 60,
      ma120: 120
    };
    
    // 计算并绘制各种均线
    Object.keys(maSettings).forEach(maKey => {
      if (maSettings[maKey]) { // 如果该均线设置为显示
        const period = maPeriods[maKey];
        const maValues = calculateMA(stockData, period); // 使用完整数据计算均线
        
        ctx.strokeStyle = maColors[maKey];
        ctx.lineWidth = 1; // 根据规范，均线线宽应为1像素
        ctx.beginPath();
        
        let firstPoint = true;
        for (let i = 0; i < pointsCount; i++) {
          const actualIndex = zoomRange.start + i;
          const maValue = maValues[actualIndex];
          if (maValue === null || isNaN(maValue)) continue;
          
          const x = margin.left + (i * chartWidth / (pointsCount - 1));
          const y = margin.top + ((maxPrice - maValue) / priceRange) * kLineHeight;
          
          if (firstPoint) {
            ctx.moveTo(x, y);
            firstPoint = false;
          } else {
            ctx.lineTo(x, y);
          }
        }
        
        ctx.stroke();
      }
    });
    
    // 绘制交易量柱状图（带颜色深浅表示成交额大小）
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      const barHeight = (point.volume / maxVolume) * volumeHeight;
      const y = margin.top + kLineHeight + gap + volumeHeight - barHeight;
      
      // 设置颜色 (根据涨跌)
      const isUp = point.close >= point.open;
      const baseColor = isUp ? [239, 83, 80] : [102, 187, 106]; // RGB values
      
      // 根据成交额调整颜色深浅
      const amountRatio = point.amount / maxAmount;
      const alpha = 0.3 + 0.7 * amountRatio; // 透明度范围 0.3 - 1.0
      
      ctx.fillStyle = `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${alpha})`;
      
      // 绘制柱状图
      ctx.fillRect(x - barWidth/2, y, barWidth, barHeight);
    }
    
    // 绘制CCI图表
    // 绘制100和-100参考线
    const yCci100 = margin.top + kLineHeight + gap + volumeHeight + gap + 
                   ((maxCci - 100) / cciRange) * cciHeight;
    const yCciMinus100 = margin.top + kLineHeight + gap + volumeHeight + gap + 
                        ((maxCci - (-100)) / cciRange) * cciHeight;
    
    ctx.strokeStyle = '#888888'; // 灰色，符合CCI参考线视觉规范
    ctx.lineWidth = 1.5; // 稍粗的线条
    ctx.setLineDash([]); // 实线
    
    // 100参考线
    ctx.beginPath();
    ctx.moveTo(margin.left, yCci100);
    ctx.lineTo(margin.left + chartWidth, yCci100);
    ctx.stroke();
    
    // -100参考线
    ctx.beginPath();
    ctx.moveTo(margin.left, yCciMinus100);
    ctx.lineTo(margin.left + chartWidth, yCciMinus100);
    ctx.stroke();
    
    ctx.lineWidth = 1; // 恢复默认线宽
    
    // 绘制CCI曲线
    ctx.strokeStyle = '#4682b4';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    let firstPoint = true;
    let hasValidCciData = false;
    const cciPoints = []; // 存储CCI点用于绘制信号箭头
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      // 检查CCI值是否有效
      if (point.cci === null || point.cci === undefined || isNaN(point.cci)) continue;
      
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + 
                ((maxCci - point.cci) / cciRange) * cciHeight;
      
      // 检查坐标是否有效
      if (isNaN(x) || isNaN(y)) continue;
      
      // 存储CCI点用于后续处理
      cciPoints.push({ x, y, cci: point.cci, index: i });
      
      if (firstPoint) {
        ctx.moveTo(x, y);
        firstPoint = false;
        hasValidCciData = true;
      } else {
        ctx.lineTo(x, y);
      }
    }
    
    // 只有当有有效数据时才绘制线条
    if (hasValidCciData) {
      ctx.stroke();
      
      // 绘制CCI信号箭头
      drawCCISignals(ctx, cciPoints, yCci100, yCciMinus100, margin);
    }
    ctx.lineWidth = 1;
    
    // 绘制KDJ图表
    // 绘制KDJ参考线 (20和80)
    const yKdj20 = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + 
                  ((maxKdj - 20) / kdjRange) * kdjHeight;
    const yKdj80 = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + 
                  ((maxKdj - 80) / kdjRange) * kdjHeight;
    
    ctx.strokeStyle = '#888888'; // 灰色参考线
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]); // 虚线
    
    // 20参考线
    ctx.beginPath();
    ctx.moveTo(margin.left, yKdj20);
    ctx.lineTo(margin.left + chartWidth, yKdj20);
    ctx.stroke();
    
    // 80参考线
    ctx.beginPath();
    ctx.moveTo(margin.left, yKdj80);
    ctx.lineTo(margin.left + chartWidth, yKdj80);
    ctx.stroke();
    
    ctx.setLineDash([]); // 恢复实线
    ctx.lineWidth = 1;
    
    // 绘制KDJ曲线
    // K线 - 红色
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 2;
    
    // 重置路径
    ctx.beginPath();
    
    let prevKValid = false;
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      if (point.kdj_k === null || point.kdj_k === undefined || isNaN(point.kdj_k)) {
        prevKValid = false;
        continue;
      }
      
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + 
                ((maxKdj - point.kdj_k) / kdjRange) * kdjHeight;
      
      // 检查坐标是否有效
      if (isNaN(x) || isNaN(y)) {
        prevKValid = false;
        continue;
      }
      
      if (!prevKValid) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      prevKValid = true;
    }
    ctx.stroke();
    
    // D线 - 绿色
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    
    // 重置路径
    ctx.beginPath();
    
    let prevDValid = false;
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      if (point.kdj_d === null || point.kdj_d === undefined || isNaN(point.kdj_d)) {
        prevDValid = false;
        continue;
      }
      
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + 
                ((maxKdj - point.kdj_d) / kdjRange) * kdjHeight;
      
      // 检查坐标是否有效
      if (isNaN(x) || isNaN(y)) {
        prevDValid = false;
        continue;
      }
      
      if (!prevDValid) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      prevDValid = true;
    }
    ctx.stroke();
    
    // J线 - 蓝色
    ctx.strokeStyle = '#0000ff';
    ctx.lineWidth = 2;
    
    // 重置路径
    ctx.beginPath();
    
    let prevJValid = false;
    for (let i = 0; i < pointsCount; i++) {
      const point = visibleData[i];
      if (point.kdj_j === null || point.kdj_j === undefined || isNaN(point.kdj_j)) {
        prevJValid = false;
        continue;
      }
      
      const x = margin.left + (i * chartWidth / (pointsCount - 1));
      const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + 
                ((maxKdj - point.kdj_j) / kdjRange) * kdjHeight;
      
      // 检查坐标是否有效
      if (isNaN(x) || isNaN(y)) {
        prevJValid = false;
        continue;
      }
      
      if (!prevJValid) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      prevJValid = true;
    }
    // 在绘制前检查是否有有效的点
    if (prevJValid) {
      ctx.stroke();
    }
    
    ctx.lineWidth = 1;
    
    // 绘制鼠标悬停信息
    if (hoverInfo) {
      const { dataPoint, x, y, isInKLineArea, isInVolumeArea } = hoverInfo;
      
      // 绘制十字线
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      
      // 垂直线
      ctx.beginPath();
      ctx.moveTo(x, margin.top);
      ctx.lineTo(x, margin.top + kLineHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap + volumeHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap);
      ctx.lineTo(x, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + gap + kdjHeight);
      ctx.stroke();
      
      // 水平线
      if (isInKLineArea) {
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(margin.left + chartWidth, y);
        ctx.stroke();
      }
      
      ctx.setLineDash([]);
      
      // 绘制提示框
      const tooltipPadding = 5;
      const tooltipWidth = 200;
      const tooltipHeight = 240; // 增加高度以容纳KDJ信息
      const tooltipX = x > width / 2 ? x - tooltipWidth - 10 : x + 10;
      const tooltipY = y > height / 2 ? y - tooltipHeight - 10 : y + 10;
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
      ctx.strokeStyle = '#000';
      ctx.strokeRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
      
      ctx.fillStyle = '#000';
      ctx.font = '12px Arial';
      ctx.textAlign = 'left';
      
      // dataPoint.date 已经是Date对象
      const dateStr = `${dataPoint.date.getFullYear()}-${dataPoint.date.getMonth()+1}-${dataPoint.date.getDate()}`;
      ctx.fillText(`日期: ${dateStr}`, tooltipX + tooltipPadding, tooltipY + 15);
      ctx.fillText(`开盘: ${dataPoint.open.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 30);
      ctx.fillText(`最高: ${dataPoint.high.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 45);
      ctx.fillText(`最低: ${dataPoint.low.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 60);
      ctx.fillText(`收盘: ${dataPoint.close.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 75);
      ctx.fillText(`成交量: ${(dataPoint.volume/1000000).toFixed(2)}M`, tooltipX + tooltipPadding, tooltipY + 90);
      ctx.fillText(`成交额: ${(dataPoint.amount/100000000).toFixed(2)}亿`, tooltipX + tooltipPadding, tooltipY + 105);
      ctx.fillText(`换手率: ${dataPoint.turn.toFixed(2)}%`, tooltipX + tooltipPadding, tooltipY + 120);
      
      // 显示涨跌信息
      const changeText = `涨跌额: ${dataPoint.change >= 0 ? '+' : ''}${dataPoint.change.toFixed(2)}`;
      const changePercentText = `涨跌幅: ${dataPoint.changePercent >= 0 ? '+' : ''}${dataPoint.changePercent.toFixed(2)}%`;
      ctx.fillText(changeText, tooltipX + tooltipPadding, tooltipY + 135);
      ctx.fillText(changePercentText, tooltipX + tooltipPadding, tooltipY + 150);
      
      ctx.fillText(`市盈率: ${dataPoint.peTTM.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 165);
      ctx.fillText(`市净率: ${dataPoint.pbMRQ.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 180);
      ctx.fillText(`市销率: ${dataPoint.psTTM.toFixed(2)}`, tooltipX + tooltipPadding, tooltipY + 195);
      
      // 显示CCI信息
      const cciText = dataPoint.cci !== null && dataPoint.cci !== undefined ? `CCI: ${dataPoint.cci.toFixed(2)}` : 'CCI: N/A';
      ctx.fillText(cciText, tooltipX + tooltipPadding, tooltipY + 210);
      
      // 显示KDJ信息
      const kdjText = `K: ${dataPoint.kdj_k !== null && dataPoint.kdj_k !== undefined ? dataPoint.kdj_k.toFixed(2) : 'N/A'}, D: ${dataPoint.kdj_d !== null && dataPoint.kdj_d !== undefined ? dataPoint.kdj_d.toFixed(2) : 'N/A'}, J: ${dataPoint.kdj_j !== null && dataPoint.kdj_j !== undefined ? dataPoint.kdj_j.toFixed(2) : 'N/A'}`;
      ctx.fillText(kdjText, tooltipX + tooltipPadding, tooltipY + 225);
    }
    
    // 添加标题
    ctx.fillStyle = '#000';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(`${selectedCode} - ${stockName}`, margin.left, margin.top - 5);
    
    // 添加操作提示
    ctx.fillStyle = '#666';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';
    ctx.fillText('滚动鼠标缩放，拖拽移动视图', width - margin.right, margin.top - 5);
    
    return canvasElement;
  };
  
  return drawChart();
};