import { Button, Paper, Typography, Box } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const { loginWithGoogle, loginDev } = useAuth()
  const navigate = useNavigate()

  async function handleLogin() {
    await loginWithGoogle()
    navigate('/')
  }

  async function handleDevLogin() {
    await loginDev()
    navigate('/')
  }

  return (
    <Box display="flex" justifyContent="center" mt={8}>
      <Paper sx={{ p: 4, textAlign: 'center' }} elevation={3}>
        <Typography variant="h5" mb={2}>Sign in</Typography>
        <Button variant="contained" startIcon={<GoogleIcon />} onClick={handleLogin} sx={{ mb: 2 }}>
          Continue with Google
        </Button>
        <br />
        <Button variant="outlined" onClick={handleDevLogin} color="secondary">
          Dev Login (No Firebase)
        </Button>
      </Paper>
    </Box>
  )
}
