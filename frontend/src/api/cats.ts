import api from './index'

export const getCats = (userId: number) => {
  return api.get('/api/cats/', { params: { user_id: userId } }).then(res => res.data)
}

export const createCat = (userId: number, cat: any) => {
  return api.post('/api/cats/', cat, { params: { user_id: userId } }).then(res => res.data)
}

export const updateCat = (catId: number, cat: any) => {
  return api.put(`/api/cats/${catId}`, cat).then(res => res.data)
}

export const deleteCat = (catId: number) => {
  return api.delete(`/api/cats/${catId}`).then(res => res.data)
}
