import axios from 'axios'
import { useUserStore } from '../stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// 认证相关
export const authApi = {
  register: (username: string, password: string) => 
    api.post('/auth/register', { username, password }),
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password })
}

// 猫咪相关
export const catApi = {
  getCats: (userId: number) => 
    api.get('/cats/', { params: { user_id: userId } }),
  createCat: (userId: number, data: any) => 
    api.post('/cats/', data, { params: { user_id: userId } }),
  updateCat: (catId: number, data: any) => 
    api.put(`/cats/${catId}`, data),
  deleteCat: (catId: number) => 
    api.delete(`/cats/${catId}`)
}

// 体重相关
export const weightApi = {
  getWeights: (catId: number) => 
    api.get(`/cats/${catId}/weights`),
  addWeight: (catId: number, data: any) => 
    api.post(`/cats/${catId}/weights`, data),
  getChartData: (userId: number) => 
    api.get('/weights/chart', { params: { user_id: userId } })
}
