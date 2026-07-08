import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../api/client'
import { signInWithGoogle } from '../api/firebase'

interface User {
  id: string
  email: string
  display_name: string | null
  role: 'admin' | 'client'
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  loginWithGoogle: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    api.get('/auth/me').then((res) => setUser(res.data)).catch(() => {
      localStorage.removeItem('access_token')
    }).finally(() => setLoading(false))
  }, [])

async function loginWithGoogle() {
  try {
    const idToken = await signInWithGoogle()
    console.log('[Auth] Got Firebase ID token, length:', idToken?.length)

    const res = await api.post('/auth/google', { id_token: idToken })
    console.log('[Auth] /auth/google success:', res.data)

    localStorage.setItem('access_token', res.data.access_token)
    setUser(res.data.user)
  } catch (err: any) {
    console.error('[Auth] loginWithGoogle failed')
    console.error('[Auth] status:', err?.response?.status)
    console.error('[Auth] response body:', err?.response?.data)
    console.error('[Auth] request payload sent:', err?.config?.data)
    throw err
  }
}

  function logout() {
    localStorage.removeItem('access_token')
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
