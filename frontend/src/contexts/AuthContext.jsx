import { createContext, useContext, useState, useEffect } from 'react'
import { authApi, userApi } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      userApi.getMe()
        .then((res) => {
          setUser(res.data)
          localStorage.setItem('user', JSON.stringify(res.data))
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const res = await authApi.login(email, password)
    localStorage.setItem('token', res.data.access_token)
    const profileRes = await userApi.getMe()
    setUser(profileRes.data)
    localStorage.setItem('user', JSON.stringify(profileRes.data))
    return profileRes.data
  }

  const register = async (name, email, password) => {
    const res = await authApi.register({ name, email, password })
    localStorage.setItem('token', res.data.access_token)
    const profileRes = await userApi.getMe()
    setUser(profileRes.data)
    localStorage.setItem('user', JSON.stringify(profileRes.data))
    // Retourne l'email pour redirection vers la vérification OTP
    return { ...profileRes.data, email }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const refreshUser = async () => {
    const res = await userApi.getMe()
    setUser(res.data)
    localStorage.setItem('user', JSON.stringify(res.data))
    return res.data
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
