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
        // 为布尔值设置合理默认值，如果数据库中有值则使用数据库值
        enable_price_breakout: params.enable_price_breakout ?? true,
        enable_volume_check: params.enable_volume_check ?? true,
        enable_cci_check: params.enable_cci_check ?? true,
        enable_ma_alignment: params.enable_ma_alignment ?? true
      })
      setActiveTab('right_side')
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
      await tradingStrategyService.executeStrategy(id)
      message.success('Strategy executed successfully')
    } catch (error) {
      message.error('Failed to execute strategy')
    }
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
      fetchStrategies()
    } catch (error) {
      console.error('Failed to save strategy:', error);
      message.error('Failed to save strategy: ' + (error.response?.data?.detail || error.message || 'Unknown error'))
    }
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setEditingStrategy(null)
    form.resetFields()
    rightSideForm.resetFields()
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