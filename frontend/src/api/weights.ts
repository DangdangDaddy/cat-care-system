import api from './index'

export const getWeights = (catId: number) => {
  return api.get(`/api/cats/${catId}/weights`).then((res: any) => res.data)
}

export const addWeight = (catId: number, date: string, weight: number) => {
  return api.post(`/api/cats/${catId}/weights`, { date, weight }).then((res: any) => res.data)
}

export const getChartData = (userId: number) => {
  return api.get('/api/weights/chart', { params: { user_id: userId } }).then((res: any) => res.data)
}
