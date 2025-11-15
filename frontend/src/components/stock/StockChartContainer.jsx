import React, { useEffect, useRef, useState } from 'react';
import { Radio, Checkbox } from 'antd';
import { drawStockChart } from './stockChartUtils';

const StockChartContainer = ({ 
  stockData, 
  technicalData, 
  selectedCode, 
  stockName, 
  zoomRange, 
  hoverInfo, 
  timeFrame, 
  setTimeFrame,
  maSettings,
  setMaSettings,
  setZoomRange,
  setHoverInfo
}) => {
  const chartContainerRef = useRef(null);
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, dataIndex: 0 });

  // 均线颜色映射
  const maColors = {
    ma5: '#ff0000',   // 红色
    ma10: '#00ff00',  // 绿色
    ma15: '#0000ff',  // 蓝色
    ma20: '#ffa500',  // 橙色（加深20日均线颜色）
    ma30: '#ff00ff',  // 紫色
    ma60: '#00ffff',  // 青色
    ma120: '#ffa500'  // 橙色
  };

  // 均线标签映射
  const maLabels = {
    ma5: '5日',
    ma10: '10日',
    ma15: '15日',
    ma20: '20日',
    ma30: '30日',
    ma60: '60日',
    ma120: '120日'
  };

  // 处理鼠标滚轮事件
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
    const kLineHeight = chartHeight * 0.35; // K线图高度占比
    const volumeHeight = chartHeight * 0.20; // 交易量图高度占比
    const gap = chartHeight * 0.02; // 图表间间距
    
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

  useEffect(() => {
    if (stockData.length > 0 && chartContainerRef.current) {
      const canvas = drawStockChart(
        canvasRef.current,
        chartContainerRef,
        stockData,
        technicalData,
        selectedCode,
        stockName,
        zoomRange,
        hoverInfo,
        timeFrame,
        maSettings
      );
      
      // 保存canvas引用
      canvasRef.current = canvas;
      
      // 添加事件监听器
      if (canvas) {
        canvas.addEventListener('wheel', handleWheel, { passive: false });
        canvas.addEventListener('mousedown', handleMouseDown);
        canvas.addEventListener('mousemove', handleMouseMove);
        canvas.addEventListener('mouseup', handleMouseUp);
        canvas.addEventListener('mouseleave', handleMouseUp);
      }
    }
    
    // 清理事件监听器
    return () => {
      if (canvasRef.current) {
        canvasRef.current.removeEventListener('wheel', handleWheel);
        canvasRef.current.removeEventListener('mousedown', handleMouseDown);
        canvasRef.current.removeEventListener('mousemove', handleMouseMove);
        canvasRef.current.removeEventListener('mouseup', handleMouseUp);
        canvasRef.current.removeEventListener('mouseleave', handleMouseUp);
      }
    };
  }, [stockData, technicalData, selectedCode, stockName, zoomRange, hoverInfo, timeFrame, maSettings, isDragging, dragStart]);

  return (
    <div>
      <div style={{ marginBottom: 10, display: 'flex', justifyContent: 'space-between' }}>
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
        
        {/* 均线控制图例 */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: 10 }}>均线:</span>
          {Object.keys(maSettings).map(maKey => (
            <div 
              key={maKey} 
              style={{ display: 'flex', alignItems: 'center', marginRight: 15 }}
            >
              <Checkbox
                checked={maSettings[maKey]}
                onChange={e => setMaSettings(prev => ({ ...prev, [maKey]: e.target.checked }))}
                style={{ marginRight: 5 }}
              />
              <div 
                style={{ 
                  width: 20, 
                  height: 2, 
                  backgroundColor: maColors[maKey], 
                  display: 'inline-block',
                  marginRight: 5 
                }} 
              />
              <span>{maLabels[maKey]}</span>
            </div>
          ))}
        </div>
      </div>
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: '100%', 
          height: 800,
          border: '1px solid #ddd',
          borderRadius: 4
        }}
      />
      <div style={{ 
        marginTop: 10, 
        fontSize: 12, 
        color: '#666',
        padding: '10px',
        border: '1px dashed #ccc',
        borderRadius: '4px',
        backgroundColor: '#f9f9f9'
      }}>
        <p>操作说明：滚动鼠标可缩放图表，按住鼠标左键可拖拽移动视图</p>
      </div>
    </div>
  );
};

export default StockChartContainer;