import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Typography, Paper, TextField, MenuItem, Button, Stack,
  FormControlLabel, Switch, Table, TableHead, TableRow, TableCell, TableBody, Chip,
} from '@mui/material'
import { api } from '../../api/client'

const ARCHITECTURES = ['EfficientNetB0', 'ResNet50', 'MobileNetV2']
const OPTIMIZERS = ['adam', 'sgd', 'rmsprop']

export default function Training() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    model_architecture: 'EfficientNetB0',
    epochs: 50,
    batch_size: 32,
    learning_rate: 0.001,
    optimizer: 'adam',
    augmentation: true,
  })

  const { data: jobs } = useQuery({
    queryKey: ['training-jobs'],
    queryFn: () => api.get('/training/jobs').then((r) => r.data),
    refetchInterval: 5000,
  })

  const startTraining = useMutation({
    mutationFn: () => api.post('/training/jobs', form),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['training-jobs'] }),
  })

  return (
    <>
      <Typography variant="h4" mb={3}>Model Training</Typography>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Stack spacing={2} maxWidth={400}>
          <TextField select label="Model" value={form.model_architecture}
            onChange={(e) => setForm({ ...form, model_architecture: e.target.value })}>
            {ARCHITECTURES.map((a) => <MenuItem key={a} value={a}>{a}</MenuItem>)}
          </TextField>
          <TextField type="number" label="Epochs" value={form.epochs}
            onChange={(e) => setForm({ ...form, epochs: Number(e.target.value) })} />
          <TextField type="number" label="Batch Size" value={form.batch_size}
            onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })} />
          <TextField type="number" label="Learning Rate" value={form.learning_rate}
            inputProps={{ step: 0.0001 }}
            onChange={(e) => setForm({ ...form, learning_rate: Number(e.target.value) })} />
          <TextField select label="Optimizer" value={form.optimizer}
            onChange={(e) => setForm({ ...form, optimizer: e.target.value })}>
            {OPTIMIZERS.map((o) => <MenuItem key={o} value={o}>{o}</MenuItem>)}
          </TextField>
          <FormControlLabel
            control={<Switch checked={form.augmentation} onChange={(e) => setForm({ ...form, augmentation: e.target.checked })} />}
            label="Augmentation"
          />
          <Button variant="contained" onClick={() => startTraining.mutate()} disabled={startTraining.isPending}>
            Train Model
          </Button>
        </Stack>
      </Paper>

      <Typography variant="h6" mb={1}>Recent Jobs</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Architecture</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Accuracy</TableCell>
            <TableCell>Created</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs?.map((j: any) => (
            <TableRow key={j.id}>
              <TableCell>{j.model_architecture}</TableCell>
              <TableCell><Chip label={j.status} color={j.status === 'completed' ? 'success' : j.status === 'failed' ? 'error' : 'default'} size="small" /></TableCell>
              <TableCell>{j.metrics?.final_val_accuracy ? (j.metrics.final_val_accuracy * 100).toFixed(1) + '%' : '—'}</TableCell>
              <TableCell>{new Date(j.created_at).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}
