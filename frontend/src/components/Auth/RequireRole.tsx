import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function RequireRole({ role, children }: { role: 'admin' | 'client'; children: JSX.Element }) {
  const { user, loading } = useAuth()
  if (loading) return <div>Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to="/" replace />
  return children
}
