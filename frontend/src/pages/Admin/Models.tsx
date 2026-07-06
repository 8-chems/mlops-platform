import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Typography, Table, TableHead, TableRow, TableCell, TableBody, Chip, Button, Stack } from '@mui/material'
import { api } from '../../api/client'

export default function Models() {
  const queryClient = useQueryClient()
  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.get('/training/models').then((r) => r.data),
  })

  const promote = useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: string }) => api.post(`/training/models/${id}/promote`, { stage }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/training/models/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  })

  return (
    <>
      <Typography variant="h4" mb={3}>Model Registry</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Version</TableCell>
            <TableCell>Stage</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {models?.map((m: any) => (
            <TableRow key={m.id}>
              <TableCell>{m.name}</TableCell>
              <TableCell>v{m.version}</TableCell>
              <TableCell><Chip label={m.stage} color={m.stage === 'production' ? 'success' : m.stage === 'archived' ? 'default' : 'warning'} size="small" /></TableCell>
              <TableCell>
                <Stack direction="row" spacing={1}>
                  <Button size="small" onClick={() => promote.mutate({ id: m.id, stage: 'production' })}>Promote</Button>
                  <Button size="small" onClick={() => promote.mutate({ id: m.id, stage: 'archived' })}>Archive</Button>
                  <Button size="small" color="error" onClick={() => remove.mutate(m.id)}>Delete</Button>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}
