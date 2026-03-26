// 账单分类
export const CATEGORIES = ['餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']

// 带有"全部"选项的分类列表（用于筛选）
export const CATEGORIES_WITH_ALL = ['all', ...CATEGORIES]

// 支付平台
export const PLATFORMS = ['wechat', 'alipay', 'bank']

// 带有"全部"选项的平台列表（用于筛选）
export const PLATFORMS_WITH_ALL = ['all', ...PLATFORMS]

// 平台显示信息
export const PLATFORM_INFO = {
  wechat: { name: '微信', color: 'from-green-500 to-green-600' },
  alipay: { name: '支付宝', color: 'from-blue-500 to-blue-600' },
  bank: { name: '银行卡', color: 'from-yellow-500 to-yellow-600' }
}

// 新增账单默认值
export const DEFAULT_BILL = () => ({
  name: '',
  amount: '',
  type: 'expense',
  date: new Date().toISOString().split('T')[0],
  category: '其他',
  platform: 'wechat',
  note: ''
})

// 图表配色
export const CHART_COLORS = {
  income: ['#22c55e', '#ef4444'],
  expenseCategory: ['#f97316', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#10b981', '#f59e0b', '#06b6d4'],
  incomeCategory: ['#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#f59e0b', '#06b6d4']
}
