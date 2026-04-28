import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器 - 直接从 localStorage 读取
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,  // 直接返回 data，简化调用
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      localStorage.removeItem('username')
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
  getCat: (catId: number) => 
    api.get(`/cats/${catId}`),
  createCat: (userId: number, data: any) => 
    api.post('/cats/', data, { params: { user_id: userId } }),
  addCat: (data: any) => 
    api.post('/cats/', data, { params: { user_id: data.user_id } }),
  updateCat: (catId: number, data: any) => 
    api.put(`/cats/${catId}`, data),
  deleteCat: (catId: number) => 
    api.delete(`/cats/${catId}`),
  uploadAvatar: (catId: number, formData: FormData) => 
    api.post(`/cats/${catId}/avatar`, formData, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    }),
  uploadPhoto: (catId: number, formData: FormData) => 
    api.post(`/cats/${catId}/photos`, formData, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    }),
  updatePhotos: (catId: number, photos: string[]) => 
    api.put(`/cats/${catId}/photos`, { photos })
}

// 体重相关
export const weightApi = {
  // 获取猫咪体重记录列表
  getWeights: (catId: number) => 
    api.get(`/cats/${catId}/weights`),
  // 兼容旧方法名
  getRecords: (catId: number) => 
    api.get(`/cats/${catId}/weights`),
  // 添加体重记录
  addWeight: (catId: number, data: any) => 
    api.post(`/cats/${catId}/weights`, data),
  // 兼容旧方法名
  addRecord: (data: any) => 
    api.post(`/cats/${data.cat_id}/weights`, data),
  // 更新体重记录
  updateRecord: (weightId: number, data: any) => 
    api.put(`/weights/${weightId}`, data),
  // 删除体重记录
  deleteRecord: (weightId: number) => 
    api.delete(`/weights/${weightId}`),
  // 获取图表数据
  getChartData: (userId: number) => 
    api.get('/weights/chart', { params: { user_id: userId } }),
  // 导入导出功能
  downloadTemplate: (userId: number) => 
    api.get('/weights/template', { 
      params: { user_id: userId },
      responseType: 'blob'
    }),
  importWeights: (userId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/weights/import', formData, { 
      params: { user_id: userId },
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  exportWeights: (userId: number, catIds?: number[]) => {
    const params: any = { user_id: userId }
    if (catIds && catIds.length > 0) {
      params.cat_ids = catIds.join(',')
    }
    return api.get('/weights/export', { 
      params,
      responseType: 'blob'
    })
  }
}
