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
}

export interface StudyPlan {
  daily_word_count: number
}

export async function getWordStats(): Promise<WordStats> {
  return await axios.get('/api/words/stats')
}

export async function getTodayWords(count: number = 20): Promise<Word[]> {
  return await axios.get('/api/words/today', { params: { count } })
}

export async function getReviewWords(): Promise<UserWord[]> {
  return await axios.get('/api/words/review')
}

export async function getWordList(params?: {
  page?: number
  page_size?: number
  mastery_level?: string
  keyword?: string
}): Promise<{ total: number; items: UserWord[] }> {
  return await axios.get('/api/words/list', { params })
}

export async function studyWord(wordId: number, result: string): Promise<UserWord> {
  return await axios.post('/api/words/study', { word_id: wordId, result })
}

export async function getStudyPlan(): Promise<StudyPlan> {
  return await axios.get('/api/words/plan')
}

export async function saveStudyPlan(dailyWordCount: number): Promise<StudyPlan> {
  return await axios.post('/api/words/plan', { daily_word_count: dailyWordCount })
}
