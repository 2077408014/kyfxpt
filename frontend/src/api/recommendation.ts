import request from './axios'

export interface Recommendation {
  id: number
  user_id: number
  subject: string
  knowledge_point: string
  difficulty: string
  question_text: string
  answer: string
  analysis: string
  source: string
  completed: boolean
  result: string | null
  completion_time: string | null
  created_at: string
}

export interface WeakPoint {
  subject: string
  knowledge_point: string
  weak_level: number
  mistake_count: number
  updated_at: string
}

export interface RecommendationReport {
  total_recommendations: number
  completed_recommendations: number
  correct_recommendations: number
  accuracy_rate: number
  weak_points: WeakPoint[]
}

export interface RecommendationComplete {
  result: string
}

export async function analyzeWeakPoints(): Promise<WeakPoint[]> {
  return await request.get('/api/recommend/analysis')
}

export async function generateRecommendations(count: number = 5): Promise<Recommendation[]> {
  return await request.post(`/api/recommend/generate?count=${count}`)
}

export async function getRecommendations(completed?: boolean): Promise<Recommendation[]> {
  return await request.get('/api/recommend/list', { params: { completed } })
}

export async function completeRecommendation(id: number, result: string): Promise<Recommendation> {
  return await request.post(`/api/recommend/${id}/complete`, { result })
}

export async function getRecommendationReport(): Promise<RecommendationReport> {
  return await request.get('/api/recommend/report')
}