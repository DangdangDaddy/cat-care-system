import axios from 'axios'

const api: any = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器 - 直接从 localStorage 读取
api.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: any) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: any) => response.data,  // 直接返回 data，简化调用
  (error: any) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      localStorage.removeItem('username')
      const authPages = ['/login', '/register']
      if (!authPages.includes(window.location.pathname)) {
        window.location.href = '/login'
      }
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
  getPhotos: (catId: number) =>
    api.get(`/cats/${catId}/photos`),
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

export const photoApi = {
  getAllPhotos: (userId: number) =>
    api.get('/photos/all', { params: { user_id: userId } }),
  deletePhoto: (photoId: number, catId?: number) =>
    api.delete(`/photos/${photoId}`, { params: catId ? { cat_id: catId } : {} }),
  updatePhoto: (photoId: number, data: any) =>
    api.put(`/photos/${photoId}`, data),
  reorderPhoto: (data: any) =>
    api.post('/photos/reorder', data),
  recommendTags: (userId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', String(userId))
    return api.post('/photos/recommend-tags', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
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

export const medicalHistoryApi = {
  getRecords: (catId: number) =>
    api.get(`/cats/${catId}/medical-history`),
  getGroupRecords: (groupId: string) =>
    api.get(`/medical-history/group/${groupId}`),
  addRecord: (catId: number, data: any) =>
    api.post(`/cats/${catId}/medical-history`, data),
  addBatchRecords: (catId: number, catIds: number[], medical: any) =>
    api.post(`/cats/${catId}/medical-history/batch`, { cat_ids: catIds, medical }),
  updateRecord: (recordId: number, data: any) =>
    api.put(`/medical-history/${recordId}`, data),
  updateGroupRecords: (groupId: string, data: any) =>
    api.put(`/medical-history/group/${groupId}`, data),
  deleteRecord: (recordId: number) =>
    api.delete(`/medical-history/${recordId}`)
}

export const feedingApi = {
  getOverview: (catId: number) =>
    api.get(`/cats/${catId}/feeding/overview`),
  getPlans: (catId: number) =>
    api.get(`/cats/${catId}/feeding/plans`),
  getGroupPlans: (groupId: string) =>
    api.get(`/feeding/plans/group/${groupId}`),
  createPlan: (catId: number, data: any) =>
    api.post(`/cats/${catId}/feeding/plans`, data),
  createBatchPlans: (catId: number, catIds: number[], plan: any) =>
    api.post(`/cats/${catId}/feeding/plans/batch`, { cat_ids: catIds, plan }),
  updatePlan: (planId: number, data: any) =>
    api.put(`/feeding/plans/${planId}`, data),
  deletePlan: (planId: number) =>
    api.delete(`/feeding/plans/${planId}`),
  getRecords: (catId: number) =>
    api.get(`/cats/${catId}/feeding/records`),
  getGroupRecords: (groupId: string) =>
    api.get(`/feeding/records/group/${groupId}`),
  createRecord: (catId: number, data: any) =>
    api.post(`/cats/${catId}/feeding/records`, data),
  createBatchRecords: (catId: number, catIds: number[], record: any) =>
    api.post(`/cats/${catId}/feeding/records/batch`, { cat_ids: catIds, record }),
  updateRecord: (recordId: number, data: any) =>
    api.put(`/feeding/records/${recordId}`, data),
  deleteRecord: (recordId: number) =>
    api.delete(`/feeding/records/${recordId}`),
  getTransitions: (catId: number) =>
    api.get(`/cats/${catId}/feeding/transitions`),
  getGroupTransitions: (groupId: string) =>
    api.get(`/feeding/transitions/group/${groupId}`),
  createTransition: (catId: number, data: any) =>
    api.post(`/cats/${catId}/feeding/transitions`, data),
  createBatchTransitions: (catId: number, catIds: number[], transition: any) =>
    api.post(`/cats/${catId}/feeding/transitions/batch`, { cat_ids: catIds, transition }),
  updateTransition: (transitionId: number, data: any) =>
    api.put(`/feeding/transitions/${transitionId}`, data),
  deleteTransition: (transitionId: number) =>
    api.delete(`/feeding/transitions/${transitionId}`),
  getSupplements: (catId: number) =>
    api.get(`/cats/${catId}/feeding/supplements`),
  getGroupSupplements: (groupId: string) =>
    api.get(`/feeding/supplements/group/${groupId}`),
  createSupplement: (catId: number, data: any) =>
    api.post(`/cats/${catId}/feeding/supplements`, data),
  createBatchSupplements: (catId: number, catIds: number[], course: any) =>
    api.post(`/cats/${catId}/feeding/supplements/batch`, { cat_ids: catIds, course }),
  updateSupplement: (courseId: number, data: any) =>
    api.put(`/feeding/supplements/${courseId}`, data),
  deleteSupplement: (courseId: number) =>
    api.delete(`/feeding/supplements/${courseId}`)
}
