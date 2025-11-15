import React, { useState, useEffect, useRef } from 'react';
import { Form, Button, Card, Spin } from 'antd';
import { stockService } from '../services/api';
import StockSearch from '../components/stock/StockSearch';
import StockDetailView from '../components/stock/StockDetailView';
import StockChartContainer from '../components/stock/StockChartContainer';
import { aggregateData, normalizeStockCode, getMarketPrefix } from '../components/stock/stockDataUtils';

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
  const [searchResults, setSearchResults] = useState([]); // 搜索结果
  const [searchLoading, setSearchLoading] = useState(false); // 搜索加载状态
  const [stockInfo, setStockInfo] = useState(null); // 股票详细信息
  // 均线显示状态
  const [maSettings, setMaSettings] = useState({
    ma5: true,
    ma10: true,
    ma15: true,
    ma20: true,
    ma30: true,
    ma60: true,
    ma120: true
  });

  const searchTimeoutRef = useRef(null); // 搜索防抖定时器

  // 加载股票数据
  const loadStockData = async (code) => {
    const normalizedStockCode = normalizeStockCode(code);
    
    try {
      // 获取整合的股票数据（包括日线数据和技术指标）
      const response = await stockService.getStockIntegratedData(normalizedStockCode, {
        fields: 'date,open,close,high,low,volume,amount,turn,peTTM,pbMRQ,psTTM,pcfNcfTTM,preclose,cci,kdj_k,kdj_d,kdj_j'
      });

      console.log('Integrated data response:', response); // 调试日志

      // 检查响应结构并正确提取数据
      const responseData = response.data || response;
      const stockData = Array.isArray(responseData) ? responseData : (responseData.data || []);
      const stockName = (responseData.name || responseData.stockName || '');

      const formattedHistoryData = stockData.map(item => {
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
          kdj_k: item.kdj_k !== undefined && item.kdj_k !== null ? item.kdj_k : null, // KDJ K值
          kdj_d: item.kdj_d !== undefined && item.kdj_d !== null ? item.kdj_d : null, // KDJ D值
          kdj_j: item.kdj_j !== undefined && item.kdj_j !== null ? item.kdj_j : null, // KDJ J值
          change: change,        // 涨跌金额
          changePercent: changePercent  // 涨跌百分比
        };
      });

      // 返回完整的响应数据，包括股票名称
      return {
        code: normalizedStockCode,
        name: stockName,
        data: formattedHistoryData.reverse() // 按日期升序排列
      };
    } catch (error) {
      console.error('加载数据失败:', error);
      return { code: normalizedStockCode, name: '', data: [], total: 0 };
    }
  };

  // 加载股票详细信息
  const loadStockInfo = async (code) => {
    const normalizedStockCode = normalizeStockCode(code);
    
    try {
      const response = await stockService.getStockDetailedInfo(normalizedStockCode);
      console.log('Stock detailed info response:', response); // 调试日志
      return response;
    } catch (error) {
      console.error('加载股票详细信息失败:', error);
      return null;
    }
  };

  // 查询股票数据
  const handleQuery = async (values) => {
    const { stockCode } = values;
    if (!stockCode) return;

    // 如果输入的是6位数字，先进行搜索看是否有匹配项
    if (/^\d{6}$/.test(stockCode)) {
      try {
        const response = await stockService.getStocks({ code: stockCode });
        console.log('Stock query response:', response); // 调试日志
        // 检查响应结构并正确提取数据
        const responseData = response.data || response;
        const stocks = Array.isArray(responseData) ? responseData : (responseData.stocks || []);
        
        // 如果找到了匹配的股票，使用第一个结果
        if (stocks.length > 0) {
          const selectedStock = stocks[0];
          setLoading(true);
          const normalizedStockCode = normalizeStockCode(selectedStock.code);
          setSelectedCode(normalizedStockCode);

          try {
            // 获取整合的股票数据（包括日线数据和技术指标）
            const response = await loadStockData(selectedStock.code);
            console.log('Stock data response:', response); // 调试日志
            
            // 获取股票详细信息
            const stockInfoResponse = await loadStockInfo(selectedStock.code);
            console.log('Stock info response:', stockInfoResponse); // 调试日志
            setStockInfo(stockInfoResponse.data);
            
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
            
            // 更新表单值为选中的股票代码
            form.setFieldsValue({ stockCode: selectedStock.code });
          } catch (error) {
            console.error('查询失败:', error);
            alert('查询失败，请检查股票代码是否正确');
          } finally {
            setLoading(false);
          }
          return;
        }
      } catch (error) {
        console.error('搜索失败:', error);
      }
    }

    // 原有的查询逻辑
    setLoading(true);
    const normalizedStockCode = normalizeStockCode(stockCode);
    setSelectedCode(normalizedStockCode);

    try {
      // 获取整合的股票数据（包括日线数据和技术指标）
      const response = await loadStockData(stockCode);
      console.log('Stock data response:', response); // 调试日志
      
      // 获取股票详细信息
      const stockInfoResponse = await loadStockInfo(stockCode);
      console.log('Stock info response:', stockInfoResponse); // 调试日志
      setStockInfo(stockInfoResponse.data);
      
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

  // 搜索股票（支持拼音缩写）
  const handleSearch = async (value) => {
    // 清除之前的定时器
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // 如果输入为空，清空搜索结果
    if (!value) {
      setSearchResults([]);
      return;
    }

    // 如果输入的是6位数字，立即查询而不使用防抖
    if (/^\d{6}$/.test(value)) {
      setSearchLoading(true);
      try {
        const response = await stockService.getStocks({ code: value });
        console.log('Stock search response:', response); // 调试日志
        // 检查响应结构并正确提取数据
        const responseData = response.data || response;
        const stocks = Array.isArray(responseData) ? responseData : (responseData.stocks || []);
        setSearchResults(stocks);
        
        // 如果只有一个匹配结果，自动选择它
        if (stocks.length === 1) {
          form.setFieldsValue({ stockCode: stocks[0].code });
          setTimeout(() => {
            handleQuery({ stockCode: stocks[0].code });
          }, 0);
        }
      } catch (error) {
        console.error('搜索失败:', error);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
      return;
    }

    // 对于非6位数字的输入(如拼音缩写)，使用防抖定时器
    searchTimeoutRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const response = await stockService.getStocks({ name: value });
        console.log('Stock search by name response:', response); // 调试日志
        // 检查响应结构并正确提取数据
        const responseData = response.data || response;
        const stocks = Array.isArray(responseData) ? responseData : (responseData.stocks || []);
        setSearchResults(stocks);
        
        // 如果只有一个匹配结果，自动选择它
        if (stocks.length === 1) {
          form.setFieldsValue({ stockCode: stocks[0].code });
          setTimeout(() => {
            handleQuery({ stockCode: stocks[0].code });
          }, 0);
        }
      } catch (error) {
        console.error('搜索失败:', error);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300); // 300ms防抖延迟
  };

  // 选择股票
  const handleSelect = (value) => {
    form.setFieldsValue({ stockCode: value });
    handleQuery({ stockCode: value });
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

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>股票查看</h1>
      
      <Card style={{ marginBottom: 24 }}>
        <StockSearch 
          form={form}
          loading={loading}
          searchResults={searchResults}
          searchLoading={searchLoading}
          handleSearch={handleSearch}
          handleSelect={handleSelect}
          handleQuery={handleQuery}
        />
      </Card>

      {selectedCode && (
        <Card title={`${selectedCode} - ${stockName}`} style={{ marginBottom: 24 }}>
          <Spin spinning={loading} tip="加载图表数据...">
            {stockInfo && <StockDetailView stockInfo={stockInfo} />}
            <StockChartContainer 
              stockData={stockData}
              technicalData={technicalData}
              selectedCode={selectedCode}
              stockName={stockName}
              zoomRange={zoomRange}
              hoverInfo={hoverInfo}
              timeFrame={timeFrame}
              setTimeFrame={setTimeFrame}
              maSettings={maSettings}
              setMaSettings={setMaSettings}
            />
          </Spin>
        </Card>
      )}
    </div>
  );
};

export default StockView;