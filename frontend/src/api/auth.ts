import api from './index'

export const login = (username: string, password: string) => {
  return api.post('/api/auth/login', { username, password }).then(res => res.data)
}

export const register = (username: string, password: string) => {
  return api.post('/api/auth/register', { username, password }).then(res => res.data)
}
