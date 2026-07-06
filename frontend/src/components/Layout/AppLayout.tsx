import { AppBar, Toolbar, Typography, Button, Container } from '@mui/material'
import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
            MLOps Image Classification Platform
          </Typography>
          {user?.role === 'admin' && (
            <Button color="inherit" onClick={() => navigate('/admin')}>Admin</Button>
          )}
          {user && <Button color="inherit" onClick={() => navigate('/client')}>Predict</Button>}
          {user ? (
            <Button color="inherit" onClick={logout}>Logout ({user.email})</Button>
          ) : (
            <Button color="inherit" onClick={() => navigate('/login')}>Login</Button>
          )}
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4, mb: 4 }}>
        <Outlet />
      </Container>
    </>
  )
}
