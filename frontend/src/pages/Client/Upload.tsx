import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Typography, Paper, Button, Box, LinearProgress, Alert } from '@mui/material'
import { api } from '../../api/client'

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const predict = useMutation({
    mutationFn: (f: File) => {
      const form = new FormData()
      form.append('file', f)
      return api.post('/predict', form).then((r) => r.data)
    },
  })

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (f) {
      setFile(f)
      setPreview(URL.createObjectURL(f))
      predict.reset()
    }
  }

  return (
    <>
      <Typography variant="h4" mb={3}>Upload an Image</Typography>
      <Paper sx={{ p: 3, maxWidth: 500 }}>
        <Button variant="outlined" component="label" fullWidth>
          Choose Image
          <input type="file" accept="image/*" hidden onChange={handleFileChange} />
        </Button>

        {preview && (
          <Box mt={2}>
            <img src={preview} alt="preview" style={{ width: '100%', borderRadius: 8 }} />
          </Box>
        )}

        {file && (
          <Button variant="contained" fullWidth sx={{ mt: 2 }} onClick={() => predict.mutate(file)} disabled={predict.isPending}>
            Predict
          </Button>
        )}

        {predict.isPending && <LinearProgress sx={{ mt: 2 }} />}

        {predict.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {(predict.error as any)?.response?.data?.detail ?? 'Prediction failed'}
          </Alert>
        )}

        {predict.data && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Prediction: <strong>{predict.data.predicted_class}</strong> ({(predict.data.confidence * 100).toFixed(1)}% confidence)
          </Alert>
        )}
      </Paper>
    </>
  )
}
