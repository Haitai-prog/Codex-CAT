import { Routes, Route } from 'react-router-dom'
import ProjectListPage from './pages/ProjectListPage'
import ProjectDetailPage from './pages/ProjectDetailPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectListPage />} />
      <Route path="/project/:id" element={<ProjectDetailPage />} />
    </Routes>
  )
}
