import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/Layout/AppLayout'
import { RequireRole } from './components/Auth/RequireRole'
import Login from './pages/Login'
import Dashboard from './pages/Admin/Dashboard'
import Datasets from './pages/Admin/Datasets'
import Training from './pages/Admin/Training'
import Experiments from './pages/Admin/Experiments'
import Models from './pages/Admin/Models'
import Upload from './pages/Client/Upload'
import History from './pages/Client/History'
import Home from './pages/Home'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        <Route path="/admin" element={<RequireRole role="admin"><Dashboard /></RequireRole>} />
        <Route path="/admin/datasets" element={<RequireRole role="admin"><Datasets /></RequireRole>} />
        <Route path="/admin/training" element={<RequireRole role="admin"><Training /></RequireRole>} />
        <Route path="/admin/experiments" element={<RequireRole role="admin"><Experiments /></RequireRole>} />
        <Route path="/admin/models" element={<RequireRole role="admin"><Models /></RequireRole>} />

        <Route path="/client" element={<RequireRole role="client"><Upload /></RequireRole>} />
        <Route path="/client/history" element={<RequireRole role="client"><History /></RequireRole>} />
      </Route>
    </Routes>
  )
}
