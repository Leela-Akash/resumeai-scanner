import api from '../utils/api'

// History comes from the backend, which reads Firestore with the Admin SDK.
// The browser never talks to Firestore directly.
export async function getUserScans() {
  const { data } = await api.get('/api/history')
  return data
}
