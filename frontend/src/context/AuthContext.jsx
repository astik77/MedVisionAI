import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/client'

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
  const [token, setToken] = useState(() => localStorage.getItem('access_token'))
  const [loading, setLoading] = useState(false)

  // Verify token is still valid on mount
  useEffect(() => {
    if (token && !user) {
      authAPI.me()
        .then(({ data }) => setUser(data))
        .catch(() => logout())
    }
  }, [])

  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const { data } = await authAPI.login({ email, password })
      localStorage.setItem('access_token', data.access_token)
      setToken(data.access_token)
      // Fetch user profile
      const { data: profile } = await authAPI.me()
      setUser(profile)
      localStorage.setItem('user', JSON.stringify(profile))
      return { success: true }
    } catch (err) {
      return {
        success: false,
        message: err.response?.data?.detail || 'Login failed.',
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (email, username, password) => {
    setLoading(true)
    try {
      await authAPI.register({ email, username, password })
      // Auto-login after register
      return await login(email, password)
    } catch (err) {
      return {
        success: false,
        message: err.response?.data?.detail || 'Registration failed.',
      }
    } finally {
      setLoading(false)
    }
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
    setToken(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
