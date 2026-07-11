import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Trash2, AlertCircle, CheckCircle2, Loader2, Activity, ChevronLeft, ChevronRight } from 'lucide-react'
import Navbar from '../components/Navbar'
import { historyAPI } from '../api/client'

const CLASS_COLORS = {
  'Normal':            { text: 'text-green-400',  bg: 'bg-green-400/10',  border: 'border-green-400/20' },
  'Pneumonia':         { text: 'text-red-400',    bg: 'bg-red-400/10',    border: 'border-red-400/20'   },
  'COVID-19':          { text: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20'},
  'Pleural Effusion':  { text: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20'},
  'Cardiomegaly':      { text: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20'},
}

function HistoryCard({ item, onDelete }) {
  const [deleting, setDeleting] = useState(false)
  const c = CLASS_COLORS[item.prediction_result] || { text: 'text-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-400/20' }
  const pct = Math.round(item.confidence_score * 100)
  const date = new Date(item.timestamp)

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await historyAPI.deleteRecord(item.id)
      onDelete(item.id)
    } catch {
      setDeleting(false)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20, scale: 0.97 }}
      className="glass rounded-2xl p-5 flex items-center gap-4 hover:border-white/12 transition-all duration-200"
    >
      {/* Result badge */}
      <div className={`flex-shrink-0 w-12 h-12 rounded-xl ${c.bg} border ${c.border} flex items-center justify-center`}>
        {item.prediction_result === 'Normal'
          ? <CheckCircle2 size={20} className={c.text} />
          : <AlertCircle size={20} className={c.text} />
        }
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className={`font-semibold ${c.text}`}>{item.prediction_result}</p>
          <span className="text-xs text-slate-600">·</span>
          <span className="text-xs text-slate-500">{pct}% confidence</span>
        </div>
        {/* Mini confidence bar */}
        <div className="h-1 bg-white/5 rounded-full overflow-hidden w-32">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-cyan-300"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
        <p className="text-slate-500 text-xs mt-1.5">
          {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} · {date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      {/* Record ID */}
      <span className="text-xs text-slate-600 font-mono hidden sm:block">#{item.id}</span>

      {/* Delete */}
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="flex-shrink-0 p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-all duration-200 disabled:opacity-50"
      >
        {deleting ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
      </button>
    </motion.div>
  )
}

export default function History() {
  const [records, setRecords] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const PAGE_SIZE = 10

  const fetchHistory = async (p) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await historyAPI.getHistory(p, PAGE_SIZE)
      setRecords(data.items)
      setTotal(data.total)
    } catch {
      setError('Failed to load history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHistory(page) }, [page])

  const handleDelete = (id) => {
    setRecords((prev) => prev.filter((r) => r.id !== id))
    setTotal((t) => t - 1)
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="min-h-screen bg-grid">
      <Navbar />
      <div className="fixed top-32 right-8 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="pt-24 pb-16 px-4 sm:px-6 max-w-3xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-purple-400/10 border border-purple-400/20">
              <Clock size={18} className="text-purple-400" />
            </div>
            <h1 className="text-3xl font-bold text-white">Scan History</h1>
          </div>
          <p className="text-slate-400 text-sm ml-14">
            {total > 0 ? `${total} scan${total !== 1 ? 's' : ''} on record` : 'No scans yet'}
          </p>
        </motion.div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}>
              <Activity size={28} className="text-cyan-400" />
            </motion.div>
            <p className="text-slate-400 text-sm">Loading history...</p>
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-3 text-sm">
            <AlertCircle size={15} /> {error}
          </div>
        ) : records.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="glass rounded-3xl p-16 flex flex-col items-center gap-4 text-center"
          >
            <Clock size={40} className="text-slate-600" />
            <div>
              <p className="text-slate-400 font-medium">No scans yet</p>
              <p className="text-slate-600 text-sm mt-1">Upload a chest X-ray from the Scanner to get started</p>
            </div>
          </motion.div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {records.map((item) => (
                <HistoryCard key={item.id} item={item} onDelete={handleDelete} />
              ))}
            </AnimatePresence>

            {/* Pagination */}
            {totalPages > 1 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="flex items-center justify-center gap-3 pt-4"
              >
                <button
                  onClick={() => setPage(p => p - 1)} disabled={page === 1}
                  className="p-2 rounded-lg glass border border-white/10 text-slate-400 hover:text-white disabled:opacity-30 transition-all"
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-sm text-slate-400">
                  Page <span className="text-white font-medium">{page}</span> of {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => p + 1)} disabled={page === totalPages}
                  className="p-2 rounded-lg glass border border-white/10 text-slate-400 hover:text-white disabled:opacity-30 transition-all"
                >
                  <ChevronRight size={16} />
                </button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
