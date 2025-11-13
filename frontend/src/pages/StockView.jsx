import React, { useState, useEffect, useRef } from 'react';
import { Form, Input, Button, Card, Spin, Tooltip, Radio } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { stockService, technicalAnalysisService } from '../services/api';
import dayjs from 'dayjs';

const StockView = () => {
  const [form] = Form.useForm();
  const [stockData, setStockData] = useState([]);
  const [originalData, setOriginalData] = useState([]); // 保存原始日线数据
  const [technicalData, setTechnicalData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCode, setSelectedCode] = useState('');
  const [stockName, setStockName] = useState('');
  const [zoomRange, setZoomRange] = useState({ start: 0, end: 0 }); // 用于缩放的数据范围
  const [hoverInfo, setHoverInfo] = useState(null); // 鼠标悬停信息
  const [isDragging, setIsDragging] = useState(false); // 是否正在拖拽
  const [dragStart, setDragStart] = useState({ x: 0, dataIndex: 0 }); // 拖拽起始位置
  const [timeFrame, setTimeFrame] = useState('daily'); // 时间周期: daily, weekly, monthly, quarterly
  const chartContainerRef = useRef(null);
  const canvasRef = useRef(null);



  // 根据时间周期聚合数据
  const aggregateData = (data, frame) => {
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
  const getMarketPrefix = (code) => {
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
  const normalizeStockCode = (code) => {
    if (code.indexOf('.') !== -1) {
      return code; // 已经是标准格式
    }
    return `${getMarketPrefix(code)}.${code}`;
  };

  // 加载股票数据
  const loadStockData = async (code) => {
    const normalizedStockCode = normalizeStockCode(code);
    
    try {
      // 获取整合的股票数据（包括日线数据和技术指标）
      const response = await stockService.getStockIntegratedData(normalizedStockCode, {
        fields: 'date,open,close,high,low,volume,amount,turn,peTTM,pbMRQ,psTTM,pcfNcfTTM,preclose,cci'
      });

      const formattedHistoryData = response.data.map(item => {
        const open = parseFloat(item.open);
        const close = parseFloat(item.close);
        const preclose = parseFloat(item.preclose);
        // 基于前一天收盘价计算涨跌额和涨跌幅
        const change = close - preclose;
        const changePercent = preclose !== 0 ? (change / preclose) * 100 : 0;

        return {
          date: new Date(item.date),
          open: open,
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          close: close,
          volume: parseInt(item.volume),
          amount: parseFloat(item.amount) || 0, // 成交额
          turn: parseFloat(item.turn) || 0, // 换手率
          peTTM: parseFloat(item.peTTM) || 0, // 市盈率
          pbMRQ: parseFloat(item.pbMRQ) || 0, // 市净率
          psTTM: parseFloat(item.psTTM) || 0, // 市销率
          pcfNcfTTM: parseFloat(item.pcfNcfTTM) || 0, // 市现率
          cci: item.cci !== undefined && item.cci !== null ? item.cci : null, // CCI指标
          change: change,        // 涨跌金额
          changePercent: changePercent  // 涨跌百分比
        };
      });

      // 返回完整的响应数据，包括股票名称
      return {
        ...response,
        data: formattedHistoryData.reverse() // 按日期升序排列
      };
    } catch (error) {
      console.error('加载数据失败:', error);
      return { code: normalizedStockCode, name: '', data: [], total: 0 };
    }
  };

  // 查询股票数据
  const handleQuery = async (values) => {
    const { stockCode } = values;
    if (!stockCode) return;

    setLoading(true);
    const normalizedStockCode = normalizeStockCode(stockCode);
    setSelectedCode(normalizedStockCode);

    try {
      // 获取整合的股票数据（包括日线数据和技术指标）
      const response = await loadStockData(stockCode);
      
      // 从整合数据响应中获取股票名称
      const stockName = response.name || '';

      setOriginalData(response.data);
      setStockName(stockName);
      
      // 根据当前时间周期聚合数据
      const aggregatedData = aggregateData(response.data, timeFrame);
      setStockData(aggregatedData);
      
      // 初始化缩放范围为最近一年的数据
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(endDate.getFullYear() - 1);
      
      // 找到对应的索引范围
      let startIndex = 0;
      let endIndex = Math.max(0, aggregatedData.length - 1);
      
      // 寻找开始索引（一年以前的数据）
      for (let i = 0; i < aggregatedData.length; i++) {
        if (new Date(aggregatedData[i].date) >= startDate) {
          startIndex = i;
          break;
        }
      }
      
      setZoomRange({ 
        start: startIndex,
        end: endIndex
      });

    } catch (error) {
      console.error('查询失败:', error);
      alert('查询失败，请检查股票代码是否正确');
    } finally {
      setLoading(false);
    }
  };

  // 当时间周期改变时重新聚合数据
  useEffect(() => {
    if (originalData.length > 0) {
      const aggregatedData = aggregateData(originalData, timeFrame);
      setStockData(aggregatedData);
      
      // 初始化缩放范围为最近一年的数据
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(endDate.getFullYear() - 1);
      
      // 找到对应的索引范围
      let startIndex = 0;
      let endIndex = Math.max(0, aggregatedData.length - 1);
      
      // 寻找开始索引（一年以前的数据）
      for (let i = 0; i < aggregatedData.length; i++) {
        if (new Date(aggregatedData[i].date) >= startDate) {
          startIndex = i;
          break;
        }
      }
      
      setZoomRange({ 
        start: startIndex,
        end: endIndex
      });
    }
  }, [timeFrame, originalData]);



  // 处理鼠标滚轮缩放
  const handleWheel = (e) => {
    e.preventDefault();
    
    if (!stockData.length) return;
    
    const delta = e.deltaY > 0 ? 1 : -1;
    const zoomFactor = 0.1;
    const zoomAmount = Math.max(1, Math.floor((zoomRange.end - zoomRange.start) * zoomFactor));
    
    // 计算鼠标位置相对于图表的百分比
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const chartWidth = rect.width - 110; // 减去边距
    const mousePercent = Math.max(0, Math.min(1, (mouseX - 60) / chartWidth));
    
    if (delta > 0) {
      // 缩小视图 (显示更多数据)
      const newStart = Math.max(0, zoomRange.start - Math.floor(zoomAmount * (1 - mousePercent)));
      const newEnd = Math.min(stockData.length - 1, zoomRange.end + Math.floor(zoomAmount * mousePercent));
      
      if (newEnd - newStart > 20) { // 确保至少显示20个数据点
        setZoomRange({ start: newStart, end: newEnd });
      }
    } else {
      // 放大视图 (显示更少数据)
      const newStart = Math.min(zoomRange.end - 20, zoomRange.start + Math.floor(zoomAmount * (1 - mousePercent)));
      const newEnd = Math.max(zoomRange.start + 20, zoomRange.end - Math.floor(zoomAmount * mousePercent));
      
      setZoomRange({ start: newStart, end: newEnd });
    }
  };

  // 处理鼠标按下开始拖拽
  const handleMouseDown = (e) => {
    if (!stockData.length || zoomRange.end <= zoomRange.start) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    
    // 图表区域参数
    const margin = { top: 20, right: 50, bottom: 50, left: 60 };
    const chartWidth = rect.width - margin.left - margin.right;
    
    // 检查是否在图表区域内
    if (x < margin.left || x > rect.width - margin.right) return;
    
    // 计算当前显示的数据点数量
    const visibleDataCount = zoomRange.end - zoomRange.start + 1;
    
    // 计算鼠标位置对应的数据点索引
    const xInChart = x - margin.left;
    const dataIndex = Math.round(zoomRange.start + (xInChart / chartWidth) * (visibleDataCount - 1));
    
    setIsDragging(true);
    setDragStart({ x, dataIndex });
    canvas.style.cursor = 'grabbing'; // 设置拖拽中的光标
  };

  // 处理鼠标移动（拖拽或悬停）
  const handleMouseMove = (e) => {
    if (!stockData.length || zoomRange.end <= zoomRange.start) {
      setHoverInfo(null);
      return;
    }
    
    const canvas = canvasRef.current;
    if (!canvas) {
      setHoverInfo(null);
      return;
    }
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // 图表区域参数
    const margin = { top: 20, right: 50, bottom: 50, left: 60 };
    const chartWidth = rect.width - margin.left - margin.right;
    const chartHeight = rect.height - margin.top - margin.bottom;
    const kLineHeight = chartHeight * 0.65; // 调整K线图高度占比
    const volumeHeight = chartHeight * 0.3; // 调整成交量图高度占比
    const gap = chartHeight * 0.05; // 增加两个图表之间的间距
    
    // 检查是否在图表区域内
    if (x < margin.left || x > rect.width - margin.right || 
        y < margin.top || y > rect.height - margin.bottom) {
      setHoverInfo(null);
      return;
    }
    
    // 如果正在拖拽，处理拖拽逻辑
    if (isDragging) {
      const deltaX = dragStart.x - x;
      
      // 降低拖拽灵敏度，使拖拽更加平滑
      const sensitivity = 2; // 调整此值可以改变拖拽灵敏度，值越大越不灵敏
      if (Math.abs(deltaX) < sensitivity) return; // 忽略小幅度移动
      
      const visibleDataCount = zoomRange.end - zoomRange.start + 1;
      const dataPerPixel = visibleDataCount / chartWidth;
      const dataIndexDelta = Math.round(deltaX * dataPerPixel);
      
      const newStart = Math.max(0, Math.min(stockData.length - 1 - (zoomRange.end - zoomRange.start), zoomRange.start + dataIndexDelta));
      const newEnd = newStart + (zoomRange.end - zoomRange.start);
      
      setZoomRange({ start: newStart, end: newEnd });
      setDragStart({ x, dataIndex: dragStart.dataIndex + dataIndexDelta }); // 更新起始位置
      

      
      return;
    }
    
    // 计算当前显示的数据点数量
    const visibleDataCount = zoomRange.end - zoomRange.start + 1;
    
    // 计算鼠标位置对应的数据点索引
    const xInChart = x - margin.left;
    const dataIndex = Math.round(zoomRange.start + (xInChart / chartWidth) * (visibleDataCount - 1));
    
    // 确保索引在有效范围内
    if (dataIndex >= 0 && dataIndex < stockData.length) {
      const dataPoint = stockData[dataIndex];
      
      // 判断鼠标是否在K线区域还是成交量区域
      const isInKLineArea = y < margin.top + kLineHeight;
      const isInVolumeArea = y >= margin.top + kLineHeight + gap && y <= margin.top + kLineHeight + gap + volumeHeight;
      
      setHoverInfo({
        dataIndex,
        dataPoint,
        x,
        y,
        isInKLineArea,
        isInVolumeArea
      });
    } else {
      setHoverInfo(null);
    }
  };

  // 处理鼠标释放结束拖拽
  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      if (canvasRef.current) {
        canvasRef.current.style.cursor = 'default';
      }
    }
  };

  // 绘制K线图和交易量图
  useEffect(() => {
    if (!stockData.length || !chartContainerRef.current) return;

    const drawChart = () => {
      const container = chartContainerRef.current;
      const width = container.clientWidth;
      const height = 700; // 增加高度以容纳CCI图表
      
      // 清空容器
      container.innerHTML = '';
      
      // 创建canvas元素
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      canvas.style.display = 'block';
      canvas.style.cursor = isDragging ? 'grabbing' : 'default';
      container.appendChild(canvas);
      
      // 保存canvas引用
      canvasRef.current = canvas;
      
      const ctx = canvas.getContext('2d');
      
      // 添加事件监听器
      canvas.addEventListener('wheel', handleWheel, { passive: false });
      canvas.addEventListener('mousedown', handleMouseDown);
      canvas.addEventListener('mousemove', handleMouseMove);
      canvas.addEventListener('mouseup', handleMouseUp);
      canvas.addEventListener('mouseleave', handleMouseUp);
      
      // 设置图表参数
      const margin = { top: 20, right: 50, bottom: 50, left: 60 };
      const chartWidth = width - margin.left - margin.right;
      const chartHeight = height - margin.top - margin.bottom;
      
      // K线图区域高度 (45%)
      const kLineHeight = chartHeight * 0.45;
      // 图表间间距 (3%)
      const gap = chartHeight * 0.03;
      // 交易量图区域高度 (25%)
      const volumeHeight = chartHeight * 0.25;
      // CCI图表区域高度 (25%)
      const cciHeight = chartHeight * 0.25;
      
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
      } else {
        console.log('没有有效的CCI数据');
      }
      
      const cciRange = maxCci - minCci || 1;
      

      
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
      
      // 绘制坐标轴
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 1;
      
      // Y轴 - 价格轴
      ctx.beginPath();
      ctx.moveTo(margin.left, margin.top);
      ctx.lineTo(margin.left, margin.top + kLineHeight);
      ctx.stroke();
      
      // Y轴 - 交易量轴
      ctx.beginPath();
      ctx.moveTo(margin.left, margin.top + kLineHeight + gap);
      ctx.lineTo(margin.left, margin.top + kLineHeight + gap + volumeHeight);
      ctx.stroke();
      
      // Y轴 - CCI轴
      ctx.beginPath();
      ctx.moveTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap);
      ctx.lineTo(margin.left, margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight);
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
      }
      
      // 绘制Y轴标签 - 交易量
      for (let i = 0; i <= 3; i++) {
        const volume = maxVolume - (i * maxVolume / 3);
        const y = margin.top + kLineHeight + gap + (i * volumeHeight / 3);
        const volumeInMillions = volume / 1000000;
        ctx.fillText(volumeInMillions >= 1 ? volumeInMillions.toFixed(1) + 'M' : volume.toFixed(0), margin.left - 5, y + 4);
      }
      
      // 绘制Y轴标签 - CCI
      for (let i = 0; i <= 3; i++) {
        const cciValue = maxCci - (i * cciRange / 3);
        const y = margin.top + kLineHeight + gap + volumeHeight + gap + (i * cciHeight / 3);
        ctx.fillText(cciValue.toFixed(0), margin.left - 5, y + 4);
      }
      
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
          
          const y = margin.top + kLineHeight + gap + volumeHeight + gap + cciHeight + 15;
          ctx.fillText(label, x, y);
        }
      }
      
      // 绘制K线
      const barWidth = Math.max(1, chartWidth / pointsCount - 1);
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
      }
      
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
      
      ctx.strokeStyle = '#ff0000'; // 红色，更明显
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
      for (let i = 0; i < pointsCount; i++) {
        const point = visibleData[i];
        // 检查CCI值是否有效
        if (point.cci === null || point.cci === undefined || isNaN(point.cci)) continue;
        
        const x = margin.left + (i * chartWidth / (pointsCount - 1));
        const y = margin.top + kLineHeight + gap + volumeHeight + gap + 
                  ((maxCci - point.cci) / cciRange) * cciHeight;
        
        // 检查坐标是否有效
        if (isNaN(x) || isNaN(y)) continue;
        
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
        const tooltipHeight = 220; // 增加高度以容纳CCI信息
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
    };
    
    drawChart();
    
    const handleResize = () => {
      drawChart();
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (canvasRef.current) {
        canvasRef.current.removeEventListener('wheel', handleWheel);
        canvasRef.current.removeEventListener('mousedown', handleMouseDown);
        canvasRef.current.removeEventListener('mousemove', handleMouseMove);
        canvasRef.current.removeEventListener('mouseup', handleMouseUp);
        canvasRef.current.removeEventListener('mouseleave', handleMouseUp);
      }
    };
  }, [stockData, technicalData, selectedCode, stockName, zoomRange, hoverInfo, isDragging, timeFrame]);

  // 渲染图表容器
  const renderChart = () => {
    if (!selectedCode) return null;

    return (
      <div>
        <div style={{ marginBottom: 10 }}>
          <Radio.Group 
            value={timeFrame} 
            onChange={(e) => setTimeFrame(e.target.value)}
            style={{ marginBottom: 10 }}
          >
            <Radio.Button value="daily">日K</Radio.Button>
            <Radio.Button value="weekly">周K</Radio.Button>
            <Radio.Button value="monthly">月K</Radio.Button>
            <Radio.Button value="quarterly">季K</Radio.Button>
          </Radio.Group>
        </div>
        <div 
          ref={chartContainerRef} 
          style={{ 
            width: '100%', 
            height: 700,
            border: '1px solid #ddd',
            borderRadius: 4
          }}
        />
        <div style={{ marginTop: 10, fontSize: 12, color: '#666' }}>
          <p>操作说明：滚动鼠标可缩放图表，按住鼠标左键可拖拽移动视图</p>
        </div>
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>股票查看</h1>
      
      <Card style={{ marginBottom: 24 }}>
        <Form form={form} onFinish={handleQuery} layout="inline">
          <Form.Item name="stockCode" label="股票代码" rules={[{ required: true, message: '请输入股票代码' }]}>
            <Input placeholder="例如：sh.600066" style={{ width: 300 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
              查询
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {selectedCode && (
        <Card title={`${selectedCode} - ${stockName}`} style={{ marginBottom: 24 }}>
          <Spin spinning={loading} tip="加载图表数据...">
            {renderChart()}
          </Spin>
        </Card>
      )}
    </div>
  );
};

export default StockView;