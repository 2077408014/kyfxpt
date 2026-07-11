import axios from './axios'

export interface Mistake {
  id: number
  user_id: number
  subject: string
  knowledge_point: string | null
  error_type: string | null
  difficulty: string | null
  mastery_level: string
  question_text: string | null
  answer: string | null
  analysis: string | null
  error_reason: string | null
  image_path: string | null
  next_review_date: string | null
  review_count: number
  correct_count: number
  created_at: string
  updated_at: string | null
}

export interface MistakeCreate {
  subject: string
  knowledge_point?: string
  error_type?: string
  difficulty?: string
  question_text?: string
  answer?: string
  analysis?: string
  error_reason?: string
  image_path?: string
}

export interface MistakeReviewCreate {
  result: string
  notes?: string
}

export interface UploadResponse {
  image_path: string
  image_url: string
}

export interface RecognizeResponse {
  question_text: string | null
  subject: string | null
  knowledge_point: string | null
  confidence: number
  raw_text: string
}

export interface SimilarMistake {
  id: number
  subject: string
  knowledge_point: string | null
  question_text: string | null
  difficulty: string | null
  mastery_level: string
  similarity_score: number
}

export async function createMistake(data: MistakeCreate): Promise<Mistake> {
  const response = await axios.post('/mistakes', data)
  return response.data
}

export async function getMistakes(params?: Record<string, string>): Promise<Mistake[]> {
  const response = await axios.get('/mistakes', { params })
  return response.data
}

export async function getMistake(id: number): Promise<Mistake> {
  const response = await axios.get(`/mistakes/${id}`)
  return response.data
}

export async function updateMistake(id: number, data: Partial<MistakeCreate>): Promise<Mistake> {
  const response = await axios.put(`/mistakes/${id}`, data)
  return response.data
}

export async function deleteMistake(id: number): Promise<void> {
  await axios.delete(`/mistakes/${id}`)
}

export async function reviewMistake(id: number, data: MistakeReviewCreate): Promise<void> {
  await axios.post(`/mistakes/${id}/review`, data)
}

export async function getTodayReviews(): Promise<Mistake[]> {
  const response = await axios.get('/mistakes/review/today')
  return response.data
}

export async function uploadMistakeImage(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axios.post('/mistakes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function recognizeMistake(imagePath: string): Promise<RecognizeResponse> {
  const response = await axios.post('/mistakes/recognize', { image_path: imagePath })
  return response.data
}

export async function getSimilarMistakes(id: number): Promise<SimilarMistake[]> {
  const response = await axios.get(`/mistakes/${id}/similar`)
  return response.data
}
