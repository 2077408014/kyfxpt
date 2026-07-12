import axios from 'axios'
import router from '../router'

const instance = axios.create({
  baseURL: '',
  timeout: 30000
})

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const store = useUserStore()
      store.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default instance