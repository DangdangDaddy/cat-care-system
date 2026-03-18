export interface Cat {
  id: number
  owner_id: number
  name: string
  breed: string
  gender: string
  birth_date: string
  neutered: boolean
  avatar?: string
  created_at?: string
}

export interface HealthRecord {
  id: number
  cat_id: number
  record_type: string
  record_date: string
  description: string
  created_at?: string
}

export interface WeightRecord {
  id: number
  cat_id: number
  weight: number
  record_date: string
  notes?: string
  created_at?: string
}
