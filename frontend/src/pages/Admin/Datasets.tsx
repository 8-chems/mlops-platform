import { useState } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Typography, TextField, Button, Stack, Paper, List, ListItem, ListItemText, Input } from '@mui/material'
import { api } from '../../api/client'

interface DatasetClass { id: string; name: string; image_count: number }

export default function Datasets() {
  const queryClient = useQueryClient()
  const [newClass, setNewClass] = useState('')
  const [selectedClass, setSelectedClass] = useState<string | null>(null)

  const { data: classes } = useQuery<DatasetClass[]>({
    queryKey: ['dataset-classes'],
    queryFn: () => api.get('/datasets/classes').then((r) => r.data),
  })

  const createClass = useMutation({
    mutationFn: (name: string) => api.post('/datasets/classes', { name }),
    onSuccess: () => {
      setNewClass('')
      queryClient.invalidateQueries({ queryKey: ['dataset-classes'] })
    },
  })

  const uploadImage = useMutation({
    mutationFn: ({ classId, file }: { classId: string; file: File }) => {
      const form = new FormData()
      form.append('file', file)
      return api.post(`/datasets/classes/${classId}/images`, form)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dataset-classes'] }),
  })

  return (
    <>
      <Typography variant="h4" mb={3}>Dataset Management</Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2}>
          <TextField label="New class name" value={newClass} onChange={(e) => setNewClass(e.target.value)} size="small" />
          <Button variant="contained" disabled={!newClass} onClick={() => createClass.mutate(newClass)}>
            Create Class
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <List>
          {classes?.map((c) => (
            <ListItem
              key={c.id}
              secondaryAction={
                <Input
                  type="file"
                  onChange={(e) => {
                    const file = (e.target as HTMLInputElement).files?.[0]
                    if (file) uploadImage.mutate({ classId: c.id, file })
                  }}
                />
              }
            >
              <ListItemText primary={c.name} secondary={`${c.image_count} images`} />
            </ListItem>
          ))}
        </List>
      </Paper>
    </>
  )
}
