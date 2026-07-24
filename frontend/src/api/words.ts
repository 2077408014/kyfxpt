import axios from './axios'

export interface Word {
  id: number
  word: string
  phonetic: string | null
  meaning: string
  example_sentence: string | null
  difficulty: number
  frequency: number
  exam_requirement: string
  category?: string
  type?: string
}

export interface UserWord {
  id: number
  word_id: number
  word: string
  phonetic?: string
  meaning?: string
  example_sentence?: string
  mastery_level: string
  next_review_date: string | null
  review_count: number
  correct_count: number
  last_study_date: string | null
}

export interface WordStats {
  total: number
  studied: number
  mastered: number
  today: number
  has_wordbook?: boolean
}

export interface StudyPlan {
  daily_word_count: number
  word_category: string | null
}

export async function getWordStats(category?: string): Promise<WordStats> {
  return await axios.get('/words/stats', { params: category ? { category } : {} })
}

export interface TodayWordsResponse {
  review: Word[]
  new: Word[]
  review_count: number
  new_count: number
  total_today: number
}

export async function getTodayWords(count: number = 20, category?: string): Promise<TodayWordsResponse> {
  return await axios.get('/words/today', { params: { count, category } })
}

export async function getDailyReviewWords(category?: string): Promise<{ words: Word[]; count: number }> {
  return await axios.get('/words/daily-review', { params: { category } })
}

export async function getWordCategories(): Promise<{ categories: string[] }> {
  return await axios.get('/words/categories')
}

export async function getReviewWords(): Promise<UserWord[]> {
  return await axios.get('/words/review')
}

export async function getWordList(params?: {
  page?: number
  page_size?: number
  mastery_level?: string
  keyword?: string
  category?: string
}): Promise<{ total: number; items: UserWord[] }> {
  return await axios.get('/words/list', { params })
}

export async function studyWord(wordId: number, result: string): Promise<UserWord> {
  return await axios.post('/words/study', { word_id: wordId, result })
}

export async function getStudyPlan(): Promise<StudyPlan> {
  return await axios.get('/words/plan')
}

export async function saveStudyPlan(dailyWordCount: number, wordCategory?: string): Promise<StudyPlan> {
  return await axios.post('/words/plan', { daily_word_count: dailyWordCount, word_category: wordCategory })
}

export interface UploadWordbookResult {
  success: boolean
  message: string
  imported_count?: number
  category?: string
}

export async function uploadWordbook(file: File, category?: string): Promise<UploadWordbookResult> {
  const formData = new FormData()
  formData.append('file', file)
  if (category) {
    formData.append('category', category)
  }
  return await axios.post('/words/upload-wordbook', formData)
}