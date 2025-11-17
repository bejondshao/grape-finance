import React, { useState, useEffect } from 'react'
import { Table, Button, Form, Input, Select, Space, message, Modal, InputNumber, Switch, Tabs, Card, Typography } from 'antd'
const { Option } = Select
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { tradingStrategyService, technicalAnalysisService } from '../services/api'

const { TextArea } = Input

const TradingStrategy = () => {
  const [strategies, setStrategies] = useState([])
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingStrategy, setEditingStrategy] = useState(null)
  const [activeTab, setActiveTab] = useState('general')
  const [form] = Form.useForm()
  const [rightSideForm] = Form.useForm()
  const [strongKForm] = Form.useForm()

  // 手动执行策略相关状态
  const [executeLoading, setExecuteLoading] = useState(false)
  const [stocks, setStocks] = useState([])
  const [selectedStocks, setSelectedStocks] = useState([])
  const [executeResults, setExecuteResults] = useState([])
  const [executeModalVisible, setExecuteModalVisible] = useState(false)
  const [strategyType, setStrategyType] = useState('right_side')
  const [executeForm] = Form.useForm()
  // 添加停止执行相关状态
  const [isExecuting, setIsExecuting] = useState(false)

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 200,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => {
        if (type === 'right_side') return '右侧交易';
        return type || '通用';
      }
    },
    {
      title: 'Conditions',
      dataIndex: 'conditions',
      key: 'conditions',
      width: 300,
      render: (conditions) => (
        <div>
          {conditions?.map((condition, index) => (
            <div key={index}>
              {condition.indicator} {condition.operator} {condition.value}
            </div>
          ))}
        </div>
      ),
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      width: 100,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Switch checked={isActive} disabled />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record._id)}
          >
            Run
          </Button>
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button 
            size="small" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record._id)}
          />
        </Space>
      ),
    },
  ]

  const fetchStrategies = async () => {
    setLoading(true)
    try {
      console.log('开始获取交易策略...')
      const response = await tradingStrategyService.getStrategies()
      console.log('API响应:', response)
      
      // 直接使用response，因为API返回的就是数组
      let strategiesData = []
      
      if (Array.isArray(response)) {
        strategiesData = response
      } else if (response && Array.isArray(response.data)) {
        strategiesData = response.data
      }
      
      console.log('处理后的策略数据:', strategiesData)
      
      const normalized = strategiesData.map(s => ({
        ...s,
        _id: s?._id != null ? String(s._id) : s?._id,
        is_active: s?.is_active === true || s?.is_active === 'true' || s?.is_active === 1
      }))
      
      console.log('标准化后的策略数据:', normalized)
      setStrategies(normalized)
    } catch (error) {
      console.error('获取策略失败:', error)
      message.error('Failed to fetch strategies')
    } finally {
      setLoading(false)
    }
  }

  const fetchIndicators = async () => {
    try {
      const response = await technicalAnalysisService.getConfiguredIndicators()
      console.log('Indicators response:', response);
      // 确保响应数据是数组类型
      // API 返回的数据结构是 { data: [...] }，我们需要提取 response.data.data 字段
      const indicatorsData = response && response.data && Array.isArray(response.data?.data) 
        ? response.data.data 
        : []
      setIndicators(indicatorsData)
    } catch (error) {
      console.error('Failed to fetch indicators:', error)
      message.error('Failed to fetch indicators')
      // 设置默认指标
      const defaultIndicators = [
        {
          _id: '1',
          name: 'CCI',
          type: 'CCI',
          description: 'Commodity Channel Index'
        },
        {
          _id: '2',
          name: 'RSI',
          type: 'RSI',
          description: 'Relative Strength Index'
        },
        {
          _id: '3',
          name: 'MACD',
          type: 'MACD',
          description: 'Moving Average Convergence Divergence'
        }
      ];
      setIndicators(defaultIndicators)
    }
  }

  useEffect(() => {
    fetchStrategies()
    fetchIndicators()
  }, [])

  const handleCreate = () => {
    setEditingStrategy(null)
    form.resetFields()
    rightSideForm.resetFields()
    strongKForm.resetFields()
    // 设置右侧交易策略的默认值
    setTimeout(() => {
      rightSideForm.setFieldsValue({
        is_active: true,
        breakout_threshold: 0,
        volume_threshold: 1.5,
        cci_threshold: -100,
        ma_periods: '5,10,20',
        // 所有开关默认开启
        enable_price_breakout: true,
        enable_volume_check: true,
        enable_cci_check: true,
        enable_ma_alignment: true
      })
    }, 100)
    setActiveTab('general')
    setModalVisible(true)
  }

  const handleEdit = (strategy) => {
    setEditingStrategy(strategy)
    if (strategy.type === 'right_side') {
      const params = strategy.parameters || {}
      rightSideForm.setFieldsValue({
        name: strategy.name,
        description: strategy.description,
        operation: strategy.operation,
        is_active: strategy.is_active,
        breakout_threshold: params.breakout_threshold ?? 0,
        volume_threshold: params.volume_threshold ?? 1.5,
        cci_threshold: params.cci_threshold ?? -100,
        ma_periods: params.ma_periods ? params.ma_periods.join(',') : '5,10,20',
        days_range: params.days_range ?? 30,
        // 为布尔值设置合理默认值，如果数据库中有值则使用数据库值
        enable_price_breakout: params.enable_price_breakout ?? true,
        enable_volume_check: params.enable_volume_check ?? true,
        enable_cci_check: params.enable_cci_check ?? true,
        enable_ma_alignment: params.enable_ma_alignment ?? true
      })
      setActiveTab('right_side')
    } else if (strategy.type === 'strong_k') {
      const params = strategy.parameters || {}
      strongKForm.setFieldsValue({
        name: strategy.name,
        description: strategy.description,
        operation: strategy.operation,
        is_active: strategy.is_active,
        initial_capital: params.initial_capital ?? 100000,
        max_position_pct: params.max_position_pct ?? 0.03,
        max_positions: params.max_positions ?? 3,
        days_range: params.days_range ?? 30
      })
      setActiveTab('strong_k')
    } else {
      form.setFieldsValue({
        ...strategy,
        is_active: strategy.is_active
      })
      setActiveTab('general')
    }
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await tradingStrategyService.deleteStrategy(id)
      message.success('Strategy deleted successfully')
      fetchStrategies()
    } catch (error) {
      message.error('Failed to delete strategy')
    }
  }

  const handleExecute = async (id) => {
    try {
      // 先获取策略信息以确定类型
      const response = await tradingStrategyService.getStrategies();
      // 确保返回的是数组
      let strategies = [];
      if (Array.isArray(response)) {
        strategies = response;
      } else if (response && Array.isArray(response.data)) {
        strategies = response.data;
      } else if (response && response.strategies && Array.isArray(response.strategies)) {
        strategies = response.strategies;
      }
      
      const strategy = strategies.find(s => s._id === id);
      
      // 为强K策略和右侧交易策略都提供直接执行支持
      if (strategy && strategy.type === 'right_side') {
        message.info('正在启动右侧交易策略执行...');
        const executeResponse = await tradingStrategyService.executeRightSideStrategy();
        if (executeResponse && executeResponse.status === 'started') {
          message.success('右侧交易策略已启动执行');
          // 开始轮询检查执行状态
          if (executeResponse.execution_id) {
            pollExecutionStatus(executeResponse.execution_id);
          }
        } else {
          message.success('右侧交易策略执行成功');
        }
      } else if (strategy && strategy.type === 'strong_k') {
        // 直接执行强K策略，使用策略中保存的参数
        message.info('正在启动强K策略执行...');
        const params = {
          strategy_type: 'strong_k',
          stock_codes: [], // 空数组表示执行所有股票
          parameters: strategy.parameters || {}
        };
        const executeResponse = await tradingStrategyService.manualExecuteStrategy(params);
        if (executeResponse && executeResponse.status === 'started') {
          message.success('强K策略已启动执行');
          // 开始轮询检查执行状态
          if (executeResponse.execution_id) {
            pollExecutionStatus(executeResponse.execution_id);
          }
        } else {
          message.success('强K策略执行成功');
        }
      } else {
        message.info('正在启动策略执行...');
        const executeResponse = await tradingStrategyService.executeStrategy(id);
        if (executeResponse && executeResponse.status === 'started') {
          message.success('策略已启动执行');
          // 开始轮询检查执行状态
          if (executeResponse.execution_id) {
            pollExecutionStatus(executeResponse.execution_id);
          }
        } else {
          message.success('策略执行成功');
        }
      }
    } catch (error) {
      message.error('Failed to execute strategy: ' + (error.response?.data?.detail || error.message));
    }
  }

  const fetchStocks = async () => {
    try {
      const response = await tradingStrategyService.filterStocks({})
      if (response && response.stocks) {
        setStocks(response.stocks)
      }
    } catch (error) {
      console.error('获取股票列表失败:', error)
      message.error('获取股票列表失败')
    }
  }

  const handleManualExecute = async (values) => {
    setExecuteLoading(true)
    setIsExecuting(true)
    try {
      const params = {
        strategy_type: strategyType,
        stock_codes: selectedStocks,
        days_range: values.days_range || 30,
        parameters: {
          initial_capital: values.initial_capital || 100000,
          max_position_pct: values.max_position_pct || 0.02,
          max_positions: values.max_positions || 5,
          ...values
        }
      }
      
      const response = await tradingStrategyService.manualExecuteStrategy(params)
      
      if (response && response.status === 'started') {
        message.success('策略执行任务已启动，请稍后查看结果');
        // 开始轮询检查执行状态
        if (response.execution_id) {
          pollExecutionStatus(response.execution_id);
        }
        // 关闭执行模态框
        closeExecuteModal();
      } else if (response && response.results) {
        setExecuteResults(response.results)
        const messageText = response.cancelled 
          ? `策略执行已取消，共处理${response.total_stocks}只股票` 
          : `策略执行完成，共处理${response.total_stocks}只股票`
        message.success(messageText)
      }
    } catch (error) {
      console.error('手动执行策略失败:', error)
      message.error('手动执行策略失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setExecuteLoading(false)
      setIsExecuting(false)
    }
  }

  const openExecuteModal = () => {
    setExecuteModalVisible(true)
    setExecuteResults([])
    setSelectedStocks([])
    fetchStocks()
  }

  const closeExecuteModal = () => {
    setExecuteModalVisible(false)
    setExecuteResults([])
    setSelectedStocks([])
    executeForm.resetFields()
  }

  // 添加停止策略执行函数
  const handleStopExecution = async () => {
    try {
      await tradingStrategyService.stopStrategyExecution()
      message.success('已发送停止执行命令')
      setIsExecuting(false)
      setExecuteLoading(false)
    } catch (error) {
      console.error('停止策略执行失败:', error)
      message.error('停止策略执行失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 添加轮询检查执行状态的函数
  const pollExecutionStatus = async (executionId) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await tradingStrategyService.getExecutionStatus(executionId);
        if (statusResponse.status === 'completed') {
          clearInterval(pollInterval);
          message.success('策略执行完成');
          // 可以在这里处理执行结果
          console.log('Execution result:', statusResponse.result);
        } else if (statusResponse.status === 'not_found') {
          clearInterval(pollInterval);
          message.error('执行任务未找到');
        }
      } catch (error) {
        clearInterval(pollInterval);
        console.error('检查执行状态失败:', error);
        message.error('检查执行状态失败: ' + (error.response?.data?.detail || error.message));
      }
    }, 5000); // 每5秒检查一次
  }

  const handleModalOk = async () => {
    try {
      let values;
      
      if (activeTab === 'right_side') {
        values = await rightSideForm.validateFields()
        console.log('Right side form values:', values); // 调试日志
        
        // 处理均线周期参数
        let maPeriods = [5, 10, 20];
        if (typeof values.ma_periods === 'string') {
          maPeriods = values.ma_periods.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p))
        } else if (Array.isArray(values.ma_periods)) {
          maPeriods = values.ma_periods;
        }
        
        // 确保布尔值正确处理 - 修复：使用实际的表单值，不添加默认值
        const getBooleanValue = (value) => {
          // 如果值已经是布尔类型，直接返回
          if (typeof value === 'boolean') {
            return value;
          }
          // 如果值是字符串"true"或"false"
          if (typeof value === 'string') {
            return value === 'true';
          }
          // 如果值是数字
          if (typeof value === 'number') {
            return value === 1;
          }
          // 如果没有值，返回false（而不是默认true）
          return value !== undefined ? value : false;
        };
        
        // 构造右侧交易策略参数 - 正确处理布尔值，确保用户输入被正确传递
        const strategyParams = {
          name: values.name,
          description: values.description,
          operation: values.operation,
          is_active: values.is_active,
          type: 'right_side',
          parameters: {
            breakout_threshold: values.breakout_threshold,
            volume_threshold: values.volume_threshold,
            cci_threshold: values.cci_threshold,
            ma_periods: maPeriods,
            days_range: values.days_range,
            // 确保布尔值正确传递（undefined/null视为false）
            enable_price_breakout: values.enable_price_breakout ?? true,
            enable_volume_check: values.enable_volume_check ?? true,
            enable_cci_check: values.enable_cci_check ?? true,
            enable_ma_alignment: values.enable_ma_alignment ?? true
          }
        }
        
        console.log('Strategy params to be sent:', strategyParams); // 调试日志
        
        if (editingStrategy) {
          // 更新策略
          await tradingStrategyService.updateStrategy(editingStrategy._id, strategyParams)
          message.success('右侧交易策略更新成功')
        } else {
          // 创建策略
          await tradingStrategyService.createRightSideStrategy(strategyParams)
          message.success('右侧交易策略创建成功')
        }
      } else if (activeTab === 'strong_k') {
        values = await strongKForm.validateFields()
        
        // 构造强K策略参数
        const strategyParams = {
          name: values.name,
          description: values.description,
          operation: values.operation,
          is_active: values.is_active,
          type: 'strong_k',
          parameters: {
            initial_capital: values.initial_capital,
            max_position_pct: values.max_position_pct,
            max_positions: values.max_positions,
            days_range: values.days_range
          }
        }
        
        if (editingStrategy) {
          // 更新策略
          await tradingStrategyService.updateStrategy(editingStrategy._id, strategyParams)
          message.success('强K策略更新成功')
        } else {
          // 创建策略
          await tradingStrategyService.createStrongKStrategy(strategyParams)
          message.success('强K策略创建成功')
        }
      } else {
        values = await form.validateFields()
        
        if (editingStrategy) {
          await tradingStrategyService.updateStrategy(editingStrategy._id, values)
          message.success('Strategy updated successfully')
        } else {
          await tradingStrategyService.createStrategy(values)
          message.success('Strategy created successfully')
        }
      }

      setModalVisible(false)
      setEditingStrategy(null)
      form.resetFields()
      rightSideForm.resetFields()
      strongKForm.resetFields()
      fetchStrategies()
    } catch (error) {
      console.error('Failed to save strategy:', error);
      const errorMessage = error.errorMessage || error.response?.data?.detail || error.message || 'Unknown error';
      message.error('Failed to save strategy: ' + errorMessage);
      
      // 如果是策略名称重复的错误，可以给用户更明确的提示
      if (errorMessage.includes('策略名称已存在') || errorMessage.includes('exists')) {
        message.info('请尝试使用不同的策略名称');
      }
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingStrategy(null)
    form.resetFields()
    rightSideForm.resetFields()
    strongKForm.resetFields()
  }

  const operationOptions = [
    { value: '关注', label: '关注' },
    { value: '密切关注', label: '密切关注' },
    { value: '建仓', label: '建仓' },
    { value: '加仓', label: '加仓' },
    { value: '减仓', label: '减仓' },
    { value: '持有', label: '持有' },
    { value: '清仓', label: '清仓' },
    { value: '清仓并关注', label: '清仓并关注' },
    { value: '清仓并密切关注', label: '清仓并密切关注' },
  ]

  const operatorOptions = [
    { value: '>', label: '大于' },
    { value: '>=', label: '大于等于' },
    { value: '<', label: '小于' },
    { value: '<=', label: '小于等于' },
    { value: '==', label: '等于' },
    { value: '!=', label: '不等于' },
  ]

  // 在组件内部定义 tabItems，确保每次渲染时都创建新的实例
  const getTabItems = () => [
    {
      key: 'general',
      label: '通用策略',
      children: (
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Strategy Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} />
          </Form.Item>

          <Form.List name="conditions">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, index) => {
                  const { key, name, ...restField } = field;
                  return (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'indicator']}
                        label={index === 0 ? 'Indicator' : ''}
                        rules={[{ required: true }]}
                      >
                        <Select placeholder="Select Indicator" style={{ width: 150 }}>
                          {indicators.map(indicator => (
                            <Option key={indicator._id} value={indicator.name}>
                              {indicator.name}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'operator']}
                        label={index === 0 ? 'Operator' : ''}
                        rules={[{ required: true }]}
                      >
                        <Select placeholder="Operator" style={{ width: 120 }}>
                          {operatorOptions.map(op => (
                            <Option key={op.value} value={op.value}>
                              {op.label}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>

                      <Form.Item
                        {...restField}
                        name={[name, 'value']}
                        label={index === 0 ? 'Value' : ''}
                        rules={[{ required: true }]}
                      >
                        <InputNumber placeholder="Value" />
                      </Form.Item>

                      <Button type="dashed" onClick={() => remove(name)}>
                        Remove
                      </Button>
                    </Space>
                  );
                })}

                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    Add Condition
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Form.Item name="operation" label="Operation" rules={[{ required: true }]}>
            <Select>
              {operationOptions.map(op => (
                <Option key={op.value} value={op.value}>
                  {op.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="is_active" label="Active" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
        </Form>
      )
    },
    {
      key: 'right_side',
      label: '右侧交易策略',
      children: (
        <Form form={rightSideForm} layout="vertical">
          <Card title="基础设置" size="small">
            <Form.Item name="name" label="策略名称" rules={[{ required: true }]}>
              <Input placeholder="例如：标准右侧交易策略" />
            </Form.Item>

            <Form.Item name="description" label="策略描述">
              <TextArea rows={3} placeholder="描述该策略的交易逻辑和适用场景" />
            </Form.Item>

            <Form.Item name="operation" label="操作建议" rules={[{ required: true }]}>
              <Select>
                {operationOptions.map(op => (
                  <Option key={op.value} value={op.value}>
                    {op.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="is_active" label="是否激活" valuePropName="checked">
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Card>

          <Card title="策略参数" size="small" style={{ marginTop: 16 }}>
            <Form.Item 
              name="breakout_threshold" 
              label="突破阈值" 
              extra="0表示突破前期高点，或设置具体价格"
            >
              <InputNumber placeholder="0" style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item 
              name="enable_price_breakout" 
              label="启用价格突破检查" 
              valuePropName="checked"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>

            <Form.Item 
              name="volume_threshold" 
              label="成交量阈值" 
              extra="例如1.5表示成交量需达到平均值的1.5倍"
            >
              <InputNumber placeholder="1.5" min={0.1} step={0.1} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item 
              name="enable_volume_check" 
              label="启用成交量检查" 
              valuePropName="checked"
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>

            <Form.Item 
              name="cci_threshold" 
              label="CCI阈值" 
              extra="CCI从该值以下向上突破时产生信号"
            >
              <InputNumber placeholder="-100" style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item 
              name="enable_cci_check" 
              label="启用CCI指标检查" 
              valuePropName="checked"
              initialValue={true}
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>

            <Form.Item 
              name="ma_periods" 
              label="均线周期" 
              extra="多个周期用逗号分隔，如：5,10,20"
            >
              <Input placeholder="5,10,20" />
            </Form.Item>

            <Form.Item 
              name="enable_ma_alignment" 
              label="启用均线排列检查" 
              valuePropName="checked"
              initialValue={true}
            >
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
            
            <Form.Item 
              name="days_range" 
              label="执行范围（天）" 
              initialValue={30}
            >
              <InputNumber style={{ width: '100%' }} min={1} max={365} />
            </Form.Item>
          </Card>
          
          <Card title="策略说明" size="small" style={{ marginTop: 16 }}>
            <p><strong>右侧交易策略原理：</strong></p>
            <p>1. 价格突破：股价突破关键阻力位（前期高点或设定价格）</p>
            <p>2. 成交量确认：突破时成交量显著放大</p>
            <p>3. 技术指标确认：CCI指标从设定阈值以下向上突破</p>
            <p>4. 均线排列：短期均线在长期均线上方（多头排列）</p>
          </Card>
        </Form>
      )
    },
    {
      key: 'strong_k',
      label: '强K突破策略',
      children: (
        <Form form={strongKForm} layout="vertical">
          <Card title="基础设置" size="small">
            <Form.Item name="name" label="策略名称" rules={[{ required: true }]}> 
              <Input placeholder="例如：标准强K突破策略" />
            </Form.Item>

            <Form.Item name="description" label="策略描述">
              <TextArea rows={3} placeholder="描述该策略的交易逻辑和适用场景" />
            </Form.Item>

            <Form.Item name="operation" label="操作建议" rules={[{ required: true }]}> 
              <Select>
                {operationOptions.map(op => (
                  <Option key={op.value} value={op.value}>
                    {op.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="is_active" label="是否激活" valuePropName="checked">
              <Switch checkedChildren="开启" unCheckedChildren="关闭" />
            </Form.Item>
          </Card>

          <Card title="策略参数" size="small" style={{ marginTop: 16 }}>
            <Form.Item 
              name="initial_capital" 
              label="初始资金" 
              initialValue={100000}
            >
              <InputNumber style={{ width: '100%' }} min={10000} step={10000} />
            </Form.Item>

            <Form.Item 
              name="max_position_pct" 
              label="单笔最大风险比例" 
              initialValue={0.03}
              extra="例如0.03表示单笔交易最大风险为总资金的3%"
            >
              <InputNumber style={{ width: '100%' }} min={0.01} max={0.1} step={0.01} />
            </Form.Item>

            <Form.Item 
              name="max_positions" 
              label="最大持仓数量" 
              initialValue={3}
            >
              <InputNumber style={{ width: '100%' }} min={1} max={20} />
            </Form.Item>
            
            <Form.Item 
              name="days_range" 
              label="执行范围（天）" 
              initialValue={30}
            >
              <InputNumber style={{ width: '100%' }} min={1} max={365} />
            </Form.Item>
          </Card>
          
          <Card title="策略说明" size="small" style={{ marginTop: 16 }}>
            <p><strong>强K突破策略原理：</strong></p>
            <p>1. 底部资金承接：恐慌性长阴后的长下影阳线</p>
            <p>2. 主力吸筹阶段：小连阳拉升，量能无大幅异动</p>
            <p>3. 左峰形成：阶段性高点后回调超过10%</p>
            <p>4. 量在价先：倍量阳线但价格未突破左峰</p>
            <p>5. 强K突破：倍量甚至天量阳线，突破左峰高点</p>
          </Card>
        </Form>
      )
    },
    {
      key: 'manual_execute',
      label: '手动执行策略',
      children: (
        <div>
          <Card title="策略执行设置" size="small">
            <Form form={executeForm} layout="vertical">
              <Form.Item name="strategy_type" label="策略类型" rules={[{ required: true }]}>
                <Select value={strategyType} onChange={setStrategyType}>
                  <Option value="right_side">右侧交易策略</Option>
                  <Option value="strong_k">强K策略</Option>
                </Select>
              </Form.Item>

              <Form.Item name="days_range" label="执行范围（天）" initialValue={30}>
                <InputNumber style={{ width: '100%' }} min={1} max={365} />
              </Form.Item>

              <Form.Item name="initial_capital" label="初始资金" initialValue={100000}>
                <InputNumber style={{ width: '100%' }} min={10000} step={10000} />
              </Form.Item>

              <Form.Item name="max_position_pct" label="最大持仓比例" initialValue={0.02}>
                <InputNumber style={{ width: '100%' }} min={0.01} max={0.1} step={0.01} />
              </Form.Item>

              <Form.Item name="max_positions" label="最大持仓数量" initialValue={5}>
                <InputNumber style={{ width: '100%' }} min={1} max={20} />
              </Form.Item>
            </Form>
          </Card>

          <Card title="股票选择" size="small" style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 16 }}>
              <Button 
                type="primary" 
                onClick={fetchStocks}
                loading={executeLoading}
              >
                刷新股票列表
              </Button>
              <span style={{ marginLeft: 16 }}>
                已选择 {selectedStocks.length} 只股票
              </span>
            </div>
            
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="选择要执行策略的股票（留空表示执行所有股票）"
              value={selectedStocks}
              onChange={setSelectedStocks}
              options={stocks.map(stock => ({
                label: `${stock.code} - ${stock.code_name}`,
                value: stock.code
              }))}
              filterOption={(input, option) =>
                option.label.toLowerCase().includes(input.toLowerCase())
              }
            />
          </Card>

          <div style={{ marginTop: 16, textAlign: 'center' }}>
            {isExecuting ? (
              <Button 
                type="primary" 
                size="large"
                danger
                onClick={handleStopExecution}
                loading={executeLoading}
              >
                停止执行
              </Button>
            ) : (
              <Button 
                type="primary" 
                size="large"
                onClick={() => executeForm.validateFields().then(handleManualExecute)}
                loading={executeLoading}
              >
                执行策略
              </Button>
            )}
          </div>

          {executeResults.length > 0 && (
            <Card title="执行结果" size="small" style={{ marginTop: 16 }}>
              <Table
                dataSource={executeResults}
                columns={[
                  { title: '股票代码', dataIndex: 'stock_code', key: 'stock_code' },
                  { 
                    title: '状态', 
                    dataIndex: 'status', 
                    key: 'status',
                    render: (status) => {
                      switch (status) {
                        case 'success':
                          return <span style={{ color: 'green' }}>有信号</span>;
                        case 'no_signals':
                          return <span style={{ color: 'orange' }}>无信号</span>;
                        case 'no_data':
                          return <span style={{ color: 'gray' }}>无数据</span>;
                        case 'error':
                          return <span style={{ color: 'red' }}>错误</span>;
                        default:
                          return <span>{status}</span>;
                      }
                    }
                  },
                  { 
                    title: '信号数量', 
                    dataIndex: 'signals', 
                    key: 'signals_count',
                    render: (signals) => signals ? signals.length : 0
                  },
                  { 
                    title: '错误', 
                    dataIndex: 'error', 
                    key: 'error',
                    render: (error) => error ? <span style={{ color: 'red' }}>{error}</span> : '-'
                  }
                ]}
                pagination={false}
                size="small"
              />
            </Card>
          )}
        </div>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Trading Strategy</h1>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Create Strategy
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={strategies}
        rowKey="_id"
        loading={loading}
        scroll={{ x: 1000 }}
      />

      <Modal
        title={editingStrategy ? 'Edit Strategy' : 'Create Strategy'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={getTabItems()} />
      </Modal>
    </div>
  )
}

export default TradingStrategy