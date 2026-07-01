import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { Project } from '../types'

export default function ProjectListPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [sourceLang, setSourceLang] = useState('en')
  const [targetLang, setTargetLang] = useState('zh')
  const navigate = useNavigate()

  const load = () => api.getProjects().then(setProjects)
  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await api.createProject({ name, source_lang: sourceLang, target_lang: targetLang })
    setName('')
    setShowCreate(false)
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this project?')) return
    await api.deleteProject(id)
    load()
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Codex CAT</h1>
        <button onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
          New Project
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-6 p-4 bg-white rounded border space-y-3">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Project name"
            className="w-full border rounded px-3 py-2 text-sm" required />
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-xs text-gray-500">Source</label>
              <input value={sourceLang} onChange={e => setSourceLang(e.target.value)}
                className="w-full border rounded px-3 py-1 text-sm" />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500">Target</label>
              <input value={targetLang} onChange={e => setTargetLang(e.target.value)}
                className="w-full border rounded px-3 py-1 text-sm" />
            </div>
          </div>
          <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
            Create
          </button>
        </form>
      )}

      <div className="space-y-3">
        {projects.map(p => (
          <div key={p.id} className="bg-white rounded border p-4 flex items-center justify-between hover:shadow-sm cursor-pointer"
            onClick={() => navigate(`/project/${p.id}`)}>
            <div>
              <div className="font-medium">{p.name}</div>
              <div className="text-sm text-gray-500">{p.source_lang} → {p.target_lang}</div>
              {p.total_segments > 0 && (
                <div className="text-xs text-gray-400 mt-1">
                  {p.translated_segments}/{p.total_segments} segments translated
                </div>
              )}
            </div>
            <button onClick={e => { e.stopPropagation(); handleDelete(p.id) }}
              className="text-red-500 hover:text-red-700 text-sm">
              Delete
            </button>
          </div>
        ))}
        {projects.length === 0 && (
          <p className="text-gray-400 text-center py-8">No projects yet. Create one to start translating.</p>
        )}
      </div>
    </div>
  )
}
