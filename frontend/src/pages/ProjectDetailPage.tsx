import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { Document, Segment, TMMatch, GlossaryTerm, GlossaryEntry } from '../types'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = Number(id)
  const [docs, setDocs] = useState<Document[]>([])
  const [activeDocId, setActiveDocId] = useState<number | null>(null)
  const [segments, setSegments] = useState<Segment[]>([])
  const [activeSid, setActiveSid] = useState<number | null>(null)
  const [matches, setMatches] = useState<TMMatch[]>([])
  const [terms, setTerms] = useState<GlossaryTerm[]>([])
  const [glossary, setGlossary] = useState<GlossaryEntry[]>([])
  const [showGlossary, setShowGlossary] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [transProgress, setTransProgress] = useState('')
  const [tokenStats, setTokenStats] = useState<{ total_calls: number; total_tokens: number } | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => { api.getDocuments(projectId).then(setDocs) }, [projectId])
  useEffect(() => { api.getGlossary().then(setGlossary); api.getTokenStats(projectId).then(s => setTokenStats({ total_calls: s.total_calls, total_tokens: s.total_tokens })).catch(() => {}) }, [])

  const loadSegments = useCallback(async (docId: number) => {
    const segs = await api.getSegments(docId)
    setSegments(segs)
    if (segs.length > 0) {
      const first = segs.find(s => s.status !== 'translated') || segs[0]
      setActiveSid(first.id)
    }
  }, [])

  useEffect(() => {
    if (activeSid) {
      api.getMatches(activeSid).then(m => setMatches(m.matches))
      api.getTerms(activeSid).then(setTerms)
    }
  }, [activeSid])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const doc = await api.uploadDocument(projectId, file)
    const updated = await api.getDocuments(projectId)
    setDocs(updated)
    setActiveDocId(doc.id)
    loadSegments(doc.id)
    e.target.value = ''
  }

  const handleSelectDoc = (docId: number) => {
    setActiveDocId(docId)
    loadSegments(docId)
  }

  const handleSegmentChange = (sid: number, targetText: string) => {
    setSegments(prev => prev.map(s => s.id === sid ? { ...s, target_text: targetText, status: 'draft' as const } : s))
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      await api.updateSegment(sid, { target_text: targetText, status: targetText.trim() ? 'translated' : 'draft' })
      setSegments(prev => prev.map(s => s.id === sid ? { ...s, status: targetText.trim() ? 'translated' as const : 'draft' as const } : s))
    }, 500)
  }

    const handlePreTranslate = async () => {
    if (!confirm('AI will translate all untranslated segments. Continue?')) return
    setTranslating(true)
    setTransProgress('Translating...')
    try {
      const result = await api.preTranslate(projectId)
      setTransProgress('Done! ' + result.translated + ' segments translated, ' + result.total_tokens + ' tokens used.')
      if (activeDocId) await loadSegments(activeDocId)
      const stats = await api.getTokenStats(projectId)
      setTokenStats({ total_calls: stats.total_calls, total_tokens: stats.total_tokens })
    } catch (e: any) {
      setTransProgress('Error: ' + (e.message || 'Unknown error'))
    }
    setTranslating(false)
  }

  const jumpToNext = () => {
    const idx = segments.findIndex(s => s.id === activeSid)
    const next = segments.slice(idx + 1).find(s => s.status !== 'translated')
      || segments.find(s => s.status !== 'translated')
    if (next) setActiveSid(next.id)
  }

  const translatedCount = segments.filter(s => s.status === 'translated').length

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-60 bg-white border-r flex flex-col shrink-0">
        <div className="p-3 border-b">
          <button onClick={() => navigate('/')} className="text-sm text-blue-600 hover:text-blue-800">&larr; Projects</button>
        </div>
        <div className="p-3 border-b">
          <label className="block text-xs font-medium text-gray-500 mb-1">Upload Document</label>
          <input type="file" accept=".txt" onChange={handleUpload} className="text-xs w-full" />
        </div>
        <div className="flex-1 overflow-y-auto">
          {docs.map(d => (
            <div key={d.id} onClick={() => handleSelectDoc(d.id)}
              className={`px-3 py-2 text-sm cursor-pointer border-b ${d.id === activeDocId ? 'bg-blue-50 border-l-2 border-l-blue-500' : 'hover:bg-gray-50'}`}>
              <div className="truncate">{d.filename}</div>
              <div className="text-xs text-gray-400">{d.segment_count} segments</div>
            </div>
          ))}
        </div>
        <div className="p-3 border-t">
          <button onClick={() => setShowGlossary(true)} className="text-xs text-gray-500 hover:text-blue-600">Glossary ({glossary.length})</button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        {segments.length > 0 && (
          <div className="bg-white border-b px-4 py-2 flex items-center justify-between shrink-0">
            <div className="text-sm text-gray-600">
              {translatedCount}/{segments.length} translated
            </div>
            <div className="w-48 bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(translatedCount / segments.length) * 100}%` }} />
            </div>
            {transProgress && (
              <div className="text-xs text-gray-500 truncate max-w-xs">{transProgress}</div>
            )}
            <div className="flex gap-2">
              <button onClick={handlePreTranslate} disabled={translating}
                className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed">
                {translating ? 'Translating...' : 'AI Pre-Translate'}
              </button>
              {tokenStats && (
                <span className="text-xs text-gray-400 self-center">Tokens: {tokenStats.total_tokens}</span>
              )}
              <button onClick={jumpToNext} className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
              Next Untranslated
            </button>
            </div>
          </div>
        )}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {segments.length === 0 && (
            <p className="text-gray-400 text-center mt-20">Upload a document to start translating</p>
          )}
          {segments.map(seg => (
            <div key={seg.id} onClick={() => setActiveSid(seg.id)}
              className={`segment-row grid grid-cols-2 gap-4 p-3 rounded border ${seg.id === activeSid ? 'active' : 'border-transparent'}`}>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{seg.source_text}</div>
              <textarea value={seg.target_text || ''} onChange={e => handleSegmentChange(seg.id, e.target.value)}
                onClick={e => { e.stopPropagation(); setActiveSid(seg.id) }}
                className="w-full border rounded p-2 text-sm resize-none min-h-[60px] focus:outline-none focus:ring-1 focus:ring-blue-400"
                placeholder="Type translation here..." />
            </div>
          ))}
        </div>
      </main>

      <aside className="w-72 bg-white border-l flex flex-col shrink-0 overflow-y-auto">
        <div className="p-3 border-b">
          <h3 className="text-sm font-semibold text-gray-700">TM Matches</h3>
        </div>
        <div className="p-2 space-y-2">
          {matches.length === 0 && <p className="text-xs text-gray-400 p-2">No matches found</p>}
          {matches.map((m, i) => (
            <div key={i} className="p-2 bg-gray-50 rounded text-xs">
              <div className="flex justify-between mb-1">
                <span className="font-medium text-gray-600">{m.score.toFixed(0)}%</span>
              </div>
              <div className="text-gray-500 mb-1">{m.source_text}</div>
              <div className="text-gray-900">{m.target_text}</div>
            </div>
          ))}
        </div>
        <div className="p-3 border-y">
          <h3 className="text-sm font-semibold text-gray-700">Glossary Terms</h3>
        </div>
        <div className="p-2 space-y-1">
          {terms.length === 0 && <p className="text-xs text-gray-400 p-2">No terms matched</p>}
          {terms.map((t, i) => (
            <div key={i} className="p-2 bg-amber-50 rounded text-xs">
              <span className="font-medium">{t.source_term}</span>
              <span className="text-gray-400 mx-1">â†?/span>
              <span>{t.target_term}</span>
              {t.note && <div className="text-gray-400 mt-0.5">{t.note}</div>}
            </div>
          ))}
        </div>
      </aside>

      {showGlossary && (
        <GlossaryModal entries={glossary} onClose={() => { setShowGlossary(false); api.getGlossary().then(setGlossary) }} />
      )}
    </div>
  )
}

function GlossaryModal({ entries, onClose }: { entries: GlossaryEntry[]; onClose: () => void }) {
  const [sLang, setSLang] = useState('en')
  const [tLang, setTLang] = useState('zh')
  const [sTerm, setSTerm] = useState('')
  const [tTerm, setTTerm] = useState('')
  const [note, setNote] = useState('')

  const add = async () => {
    if (!sTerm || !tTerm) return
    await api.createGlossaryEntry({ source_lang: sLang, target_lang: tLang, source_term: sTerm, target_term: tTerm, note: note || null })
    setSTerm(''); setTTerm(''); setNote('')
    onClose()
  }

  const remove = async (eid: number) => {
    await api.deleteGlossaryEntry(eid)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-[480px] max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="font-semibold">Glossary</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-4 space-y-2 border-b"><label className="block text-xs font-medium text-gray-500 mb-1 bg-blue-50 p-2 rounded">Import Excel (.xlsx)</label><input type="file" accept=".xlsx,.xls" onChange={async e=>{const f=e.target.files?.[0];if(f){await api.importGlossary(f);onClose()}}} className="text-xs w-full"/>
          <div className="flex gap-2">
            <input value={sLang} onChange={e => setSLang(e.target.value)} placeholder="Source lang" className="flex-1 border rounded px-2 py-1 text-xs" />
            <input value={tLang} onChange={e => setTLang(e.target.value)} placeholder="Target lang" className="flex-1 border rounded px-2 py-1 text-xs" />
          </div>
          <input value={sTerm} onChange={e => setSTerm(e.target.value)} placeholder="Source term" className="w-full border rounded px-2 py-1 text-sm" />
          <input value={tTerm} onChange={e => setTTerm(e.target.value)} placeholder="Target term" className="w-full border rounded px-2 py-1 text-sm" />
          <input value={note} onChange={e => setNote(e.target.value)} placeholder="Note (optional)" className="w-full border rounded px-2 py-1 text-xs" />
          <button onClick={add} className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700">Add</button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {entries.map(e => (
            <div key={e.id} className="flex justify-between items-center text-sm border-b pb-1">
              <div>
                <span className="font-medium">{e.source_term}</span>
                <span className="text-gray-400 mx-1">â†?/span>
                <span>{e.target_term}</span>
                <span className="text-xs text-gray-400 ml-2">[{e.source_lang}â†’{e.target_lang}]</span>
              </div>
              <button onClick={() => remove(e.id)} className="text-red-400 hover:text-red-600 text-xs">Del</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
