import api from './index'

export const login = (username: string, password: string) => {
  return api.post('/auth/login', { username, password }).then((res: any) => res.data)
}

export const register = (username: string, password: string) => {
  return api.post('/auth/register', { username, password }).then((res: any) => res.data)
}
