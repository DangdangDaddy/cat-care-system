export interface Cat {
  id: number
  owner_id: number
  name: string
  breed: string
  color?: string  // 毛色
  gender: string
  birth_date: string
  neutered: boolean
  avatar?: string
  vaccination_status?: string
  deworming_date?: string
  medical_history?: string
  internal_deworming_interval_days?: number
  external_deworming_interval_days?: number
  created_at?: string
}

export interface HealthRecord {
  id: number
  cat_id: number
  record_type: string
  sync_group_id?: string | null
  sync_group_size?: number | null
  disease: string
  date: string
  treatment?: string
  notes?: string
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
