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
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function login(data: LoginData): Promise<TokenResponse> {
  const response = await axios.post('/auth/login', data)
  return response.data
}

export async function register(data: RegisterData): Promise<User> {
  const response = await axios.post('/auth/register', data)
  return response.data
}

export async function getMe(): Promise<User> {
  const response = await axios.get('/auth/me')
  return response.data
}