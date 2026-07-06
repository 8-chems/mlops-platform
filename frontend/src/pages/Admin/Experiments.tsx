import { useQuery } from '@tanstack/react-query'
import { Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { api } from '../../api/client'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default function Experiments() {
  const { data: jobs } = useQuery({
    queryKey: ['training-jobs'],
    queryFn: () => api.get('/training/jobs').then((r) => r.data),
  })

  const completed = jobs?.filter((j: any) => j.status === 'completed') ?? []
  const latest = completed[0]
  const history = latest?.metrics?.history

  return (
    <>
      <Typography variant="h4" mb={3}>Experiments (MLflow-tracked)</Typography>

      {history && (
        <Paper sx={{ p: 2, mb: 4 }}>
          <Typography variant="h6" mb={2}>Latest run: accuracy / loss curves</Typography>
          <Line
            data={{
              labels: history.accuracy.map((_: number, i: number) => `Epoch ${i + 1}`),
              datasets: [
                { label: 'Train Accuracy', data: history.accuracy, borderColor: '#1565c0' },
                { label: 'Val Accuracy', data: history.val_accuracy, borderColor: '#00897b' },
              ],
            }}
          />
        </Paper>
      )}

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>MLflow Run</TableCell>
            <TableCell>Accuracy</TableCell>
            <TableCell>Precision</TableCell>
            <TableCell>Recall</TableCell>
            <TableCell>F1</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {completed.map((j: any) => (
            <TableRow key={j.id}>
              <TableCell>{j.mlflow_run_id?.slice(0, 8)}</TableCell>
              <TableCell>{(j.metrics?.final_val_accuracy * 100).toFixed(1)}%</TableCell>
              <TableCell>{(j.metrics?.precision * 100).toFixed(1)}%</TableCell>
              <TableCell>{(j.metrics?.recall * 100).toFixed(1)}%</TableCell>
              <TableCell>{(j.metrics?.f1 * 100).toFixed(1)}%</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}
