import { useQuery } from '@tanstack/react-query'
import { Typography, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import { api } from '../../api/client'

export default function History() {
  const { data } = useQuery({
    queryKey: ['prediction-history'],
    queryFn: () => api.get('/predict/history').then((r) => r.data),
  })

  return (
    <>
      <Typography variant="h4" mb={3}>Prediction History</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Prediction</TableCell>
            <TableCell>Confidence</TableCell>
            <TableCell>Date</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data?.map((p: any) => (
            <TableRow key={p.id}>
              <TableCell>{p.predicted_class}</TableCell>
              <TableCell>{(p.confidence * 100).toFixed(1)}%</TableCell>
              <TableCell>{new Date(p.created_at).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}
