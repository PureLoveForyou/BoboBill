import i18n from '../locales'

export const formatAmount = (amount) => {
  const currency = i18n.global.t('common.currency')
  const absAmount = Math.abs(amount)
  return amount >= 0 ? `+${currency}${absAmount.toFixed(2)}` : `-${currency}${absAmount.toFixed(2)}`
}
