import axios from './axios'

export interface LoginData {
  email: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface User {
  id: number
  username: string
  email: string
  avatar: string | null
  ai_api_provider: string | null
  ai_api_model: string | null
  ai_api_base_url: string | null
  created_at: string
}

export interface AIConfig {
  ai_api_provider?: string
  ai_api_key?: string
  ai_api_base_url?: string
  ai_api_model?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function login(data: LoginData): Promise<TokenResponse> {
  return await axios.post('/api/auth/login', data)
}

export async function register(data: RegisterData): Promise<User> {
  return await axios.post('/api/auth/register', data)
}

export async function getMe(): Promise<User> {
  return await axios.get('/api/auth/me')
}

export async function updateAIConfig(config: AIConfig): Promise<User> {
  return await axios.put('/api/auth/ai-config', config)
}