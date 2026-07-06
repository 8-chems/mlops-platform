import { useQuery } from '@tanstack/react-query'
import { Grid, Paper, Typography, Button, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => api.get('/admin/overview').then((r) => r.data),
  })

  const cards = [
    { label: 'Users', value: data?.total_users },
    { label: 'Images', value: data?.total_images },
    { label: 'Training Jobs', value: data?.total_training_jobs },
    { label: 'Predictions', value: data?.total_predictions },
  ]

  return (
    <>
      <Typography variant="h4" mb={3}>Admin Dashboard</Typography>
      <Grid container spacing={2} mb={4}>
        {cards.map((c) => (
          <Grid item xs={12} sm={3} key={c.label}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4">{c.value ?? '—'}</Typography>
              <Typography color="text.secondary">{c.label}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
      <Stack direction="row" spacing={2}>
        <Button variant="contained" onClick={() => navigate('/admin/datasets')}>Manage Datasets</Button>
        <Button variant="contained" onClick={() => navigate('/admin/training')}>Train Model</Button>
        <Button variant="contained" onClick={() => navigate('/admin/experiments')}>Experiments</Button>
        <Button variant="contained" onClick={() => navigate('/admin/models')}>Model Registry</Button>
      </Stack>
    </>
  )
}
