import React from 'react';

const StockDetailView = ({ stockInfo }) => {
  if (!stockInfo) return null;

  const { stock_info, company_info } = stockInfo;

  // 创建一个包含指定信息的数组
  const infoItems = [
    { label: '所属行业', value: stock_info?.industry },
    { label: '所在地区', value: stock_info?.area },
    { label: '公司名称', value: company_info?.com_name },
    { label: '主营业务', value: company_info?.main_business },
    { label: '公司介绍', value: company_info?.introduction },
  ];

  return (
    <div style={{ marginBottom: 20 }}>
      <h3>股票详细信息</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {infoItems.map((item, index) => (
            <tr key={index}>
              <td style={{ border: '1px solid #ddd', padding: '8px', width: '15%' }}><strong>{item.label}</strong></td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{item.value || '暂无信息'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StockDetailView;