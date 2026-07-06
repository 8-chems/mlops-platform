import { Typography } from '@mui/material'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()
  return (
    <Typography variant="h5">
      {user ? `Welcome back, ${user.display_name ?? user.email}` : 'Welcome — please log in to continue.'}
    </Typography>
  )
}
