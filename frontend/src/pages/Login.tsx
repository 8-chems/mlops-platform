import { Button, Paper, Typography, Box } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const { loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  async function handleLogin() {
    await loginWithGoogle()
    navigate('/')
  }

  return (
    <Box display="flex" justifyContent="center" mt={8}>
      <Paper sx={{ p: 4, textAlign: 'center' }} elevation={3}>
        <Typography variant="h5" mb={2}>Sign in</Typography>
        <Button variant="contained" startIcon={<GoogleIcon />} onClick={handleLogin}>
          Continue with Google
        </Button>
      </Paper>
    </Box>
  )
}
