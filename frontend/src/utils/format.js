export const formatAmount = (amount) => {
  const absAmount = Math.abs(amount)
  return amount >= 0 ? `+¥${absAmount.toFixed(2)}` : `-¥${absAmount.toFixed(2)}`
}
