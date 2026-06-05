import api from './index'

export const getCats = (userId: number) => {
  return api.get('/cats/', { params: { user_id: userId } }).then((res: any) => res.data)
}

export const createCat = (userId: number, cat: any) => {
  return api.post('/cats/', cat, { params: { user_id: userId } }).then((res: any) => res.data)
}

export const updateCat = (catId: number, cat: any) => {
  return api.put(`/cats/${catId}`, cat).then((res: any) => res.data)
}

export const deleteCat = (catId: number) => {
  return api.delete(`/cats/${catId}`).then((res: any) => res.data)
}
