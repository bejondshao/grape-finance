import React, { useEffect, useRef } from 'react';
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
  setMaSettings
}) => {
  const chartContainerRef = useRef(null);
  const canvasRef = useRef(null);

  // 均线颜色映射
  const maColors = {
    ma5: '#ff0000',   // 红色
    ma10: '#00ff00',  // 绿色
    ma15: '#0000ff',  // 蓝色
    ma20: '#ffff00',  // 黄色
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
    }
  }, [stockData, technicalData, selectedCode, stockName, zoomRange, hoverInfo, timeFrame, maSettings]);

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