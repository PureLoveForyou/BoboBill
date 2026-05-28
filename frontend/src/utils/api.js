export function getAuthHeaders(contentType = true) {
  const token = localStorage.getItem('bobobill_token')
  const headers = {}
  if (contentType) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}
