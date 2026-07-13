import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, Scan, AlertCircle, CheckCircle2,
  Activity, Zap, Brain
} from 'lucide-react'
import Navbar from '../components/Navbar'
import { useToast } from '../components/Toast'
import { predictAPI } from '../api/client'

const CLASS_COLORS = {
  'Normal':            'text-green-400',
  'Pneumonia':         'text-red-400',
  'COVID-19':          'text-orange-400',
  'Pleural Effusion':  'text-yellow-400',
  'Cardiomegaly':      'text-purple-400',
}

const CLASS_ICONS = {
  'Normal':           <CheckCircle2 size={18} />,
  'Pneumonia':        <AlertCircle size={18} />,
  'COVID-19':         <AlertCircle size={18} />,
  'Pleural Effusion': <Activity size={18} />,
  'Cardiomegaly':     <Activity size={18} />,
}

// Maps HTTP status codes to user-friendly messages
function friendlyError(err) {
  const status = err.response?.status
  const detail = err.response?.data?.detail
  if (detail && typeof detail === 'string') return detail
  switch (status) {
    case 400: return 'Invalid request. Please check the image and try again.'
    case 401: return 'Session expired. Please log in again.'
    case 413: return 'File too large. Maximum size is 10 MB.'
    case 415: return 'Unsupported file type. Please use JPEG, PNG, or WebP.'
    case 422: return 'The image could not be processed. Please try a different file.'
    case 500: return 'Server error. Our AI backend encountered an issue — please retry.'
    default:  return 'An unexpected error occurred. Please try again.'
  }
}

// ── Scanning animation overlay ─────────────────────────────────
function ScanningOverlay() {
  return (
    <div className="absolute inset-0 z-10 overflow-hidden rounded-2xl">
      <div className="absolute inset-0 bg-obsidian-900/60" />
      <div className="scan-line" />
      {['top-2 left-2', 'top-2 right-2', 'bottom-2 left-2', 'bottom-2 right-2'].map((pos, i) => (
        <div key={i} className={`absolute ${pos} w-5 h-5 border-cyan-400`}
          style={{
            borderTopWidth: i < 2 ? '2px' : '0',
            borderBottomWidth: i >= 2 ? '2px' : '0',
            borderLeftWidth: i % 2 === 0 ? '2px' : '0',
            borderRightWidth: i % 2 === 1 ? '2px' : '0',
          }} />
      ))}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-cyan-400/30 pulse-ring absolute inset-0" />
          <div className="w-12 h-12 rounded-full border-2 border-cyan-400 flex items-center justify-center">
            <Brain size={20} className="text-cyan-400" />
          </div>
        </div>
        <p className="text-cyan-400 text-sm font-mono tracking-widest animate-pulse">ANALYSING...</p>
      </div>
    </div>
  )
}

// ── Confidence bar ─────────────────────────────────────────────
function ConfidenceBar({ label, value, color, isTop }) {
  const pct = Math.round(value * 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className={`font-medium ${isTop ? color : 'text-slate-400'}`}>{label}</span>
        <span className={isTop ? color : 'text-slate-500'}>{pct}%</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${isTop
            ? 'bg-gradient-to-r from-cyan-500 to-cyan-300'
            : 'bg-white/20'}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
    </div>
  )
}

// ── Results panel ──────────────────────────────────────────────
function ResultsPanel({ result, originalUrl }) {
  const allScores = result.all_predictions ? JSON.parse(result.all_predictions) : {}
  const sorted = Object.entries(allScores).sort((a, b) => b[1] - a[1])
  const topClass = result.prediction_result
  const color = CLASS_COLORS[topClass] || 'text-cyan-400'
  const pct = Math.round(result.confidence_score * 100)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Diagnosis badge */}
      <div className="glass rounded-2xl p-5">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Diagnosis</p>
        <div className="flex items-center gap-3">
          <div className={`${color} p-2 rounded-lg bg-white/5`}>
            {CLASS_ICONS[topClass] || <Zap size={18} />}
          </div>
          <div>
            <p className={`text-xl font-bold ${color}`}>{topClass}</p>
            <p className="text-slate-400 text-sm">{pct}% confidence</p>
          </div>
        </div>
        <div className="mt-4">
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-cyan-400 to-cyan-300"
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
              style={{ boxShadow: '0 0 10px rgba(34,211,238,0.6)' }}
            />
          </div>
        </div>
      </div>

      {/* All class probabilities */}
      <div className="glass rounded-2xl p-5 space-y-3">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">All Probabilities</p>
        {sorted.map(([label, value]) => (
          <ConfidenceBar
            key={label}
            label={label}
            value={value}
            color={CLASS_COLORS[label] || 'text-cyan-400'}
            isTop={label === topClass}
          />
        ))}
      </div>

      {/* Image comparison */}
      <div className="glass rounded-2xl p-5">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Scan Comparison</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <p className="text-xs text-slate-400 text-center">Original</p>
            <img src={originalUrl} alt="Original scan" className="w-full rounded-xl object-cover aspect-square" />
          </div>
          <div className="space-y-2">
            <p className="text-xs text-cyan-400 text-center">Grad-CAM</p>
            <img
              src={`data:image/png;base64,${result.gradcam_base64}`}
              alt="Grad-CAM heatmap"
              className="w-full rounded-xl object-cover aspect-square"
              style={{ boxShadow: '0 0 12px rgba(34,211,238,0.2)' }}
            />
          </div>
        </div>
        <p className="text-xs text-slate-500 text-center mt-3">
          Heatmap highlights regions that influenced the prediction
        </p>
      </div>
    </motion.div>
  )
}

// ── Main Dashboard ─────────────────────────────────────────────
export default function Dashboard() {
  const [dragging, setDragging] = useState(false)
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef()
  const toast = useToast()

  const processFile = useCallback((f) => {
    if (!f || !f.type.startsWith('image/')) {
      const msg = 'Please upload a valid image file (JPEG, PNG, WebP).'
      setError(msg)
      toast.error(msg)
      return
    }
    setFile(f)
    setResult(null)
    setError('')
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }, [toast])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    processFile(e.dataTransfer.files[0])
  }, [processFile])

  const onFileChange = (e) => processFile(e.target.files[0])

  const handleScan = async () => {
    if (!file) return
    setScanning(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await predictAPI.predict(fd)
      setResult(data)
      const topClass = data.prediction_result
      const pct = Math.round(data.confidence_score * 100)
      toast.success(`Analysis complete — ${topClass} (${pct}%)`)
    } catch (err) {
      const msg = friendlyError(err)
      setError(msg)
      toast.error(msg)
    } finally {
      setScanning(false)
    }
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError('')
  }

  return (
    <div className="min-h-screen bg-grid">
      <Navbar />

      {/* Ambient decorations */}
      <div className="fixed top-32 left-8 w-72 h-72 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-24 right-8 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="pt-24 pb-16 px-4 sm:px-6 max-w-7xl mx-auto">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 text-center"
        >
          <div className="inline-flex items-center gap-2 bg-cyan-400/10 border border-cyan-400/20 rounded-full px-4 py-1.5 mb-4">
            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse" />
            <span className="text-cyan-400 text-xs font-mono tracking-widest uppercase">AI Scanner Online</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-3">
            Chest X-ray <span className="text-gradient-cyan">Analysis</span>
          </h1>
          <p className="text-slate-400 max-w-xl mx-auto">
            Upload a chest X-ray image and our CNN model will classify it and generate an explainable Grad-CAM heatmap.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* LEFT — Upload + controls */}
          <div className="space-y-5">
            {/* Drop zone */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => !preview && fileInputRef.current.click()}
              className={`relative rounded-3xl border-2 border-dashed transition-all duration-300 overflow-hidden cursor-pointer
                ${dragging
                  ? 'border-cyan-400 bg-cyan-400/5 scale-[1.01]'
                  : preview
                  ? 'border-white/10 cursor-default'
                  : 'border-white/15 hover:border-cyan-400/50 hover:bg-white/[0.02]'
                }`}
              style={{ minHeight: '320px' }}
            >
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />

              <AnimatePresence mode="wait">
                {preview ? (
                  <motion.div key="preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative">
                    <img src={preview} alt="Uploaded scan" className="w-full object-cover rounded-3xl" style={{ maxHeight: '380px' }} />
                    {scanning && <ScanningOverlay />}
                  </motion.div>
                ) : (
                  <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center p-12 gap-4 min-h-[320px]"
                  >
                    <div className={`p-5 rounded-2xl transition-all duration-300 ${dragging ? 'bg-cyan-400/15 glow-cyan' : 'bg-white/5'}`}>
                      <Upload size={36} className={`transition-colors duration-300 ${dragging ? 'text-cyan-400' : 'text-slate-500'}`} />
                    </div>
                    <div className="text-center">
                      <p className="text-slate-300 font-medium mb-1">Drop your X-ray image here</p>
                      <p className="text-slate-500 text-sm">or click to browse — JPEG, PNG, WebP (max 10 MB)</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Error banner */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-3 text-sm"
                >
                  <AlertCircle size={15} /> {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Action buttons */}
            {preview && !scanning && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3">
                <motion.button
                  id="scan-btn"
                  onClick={handleScan}
                  whileTap={{ scale: 0.97 }}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  <Scan size={16} /> Analyse Scan
                </motion.button>
                <button onClick={reset} className="btn-ghost px-4">Reset</button>
              </motion.div>
            )}

            {scanning && (
              <div className="flex items-center justify-center gap-3 py-3 text-cyan-400 text-sm font-mono">
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}>
                  <Scan size={16} />
                </motion.div>
                Running neural network inference...
              </div>
            )}

            {/* Stats row */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
              className="grid grid-cols-3 gap-3"
            >
              {[
                { label: 'Model', value: 'CNN', sub: 'TF/Keras' },
                { label: 'Classes', value: '5', sub: 'Pathologies' },
                { label: 'XAI', value: 'Grad-CAM', sub: 'Explanation' },
              ].map(({ label, value, sub }) => (
                <div key={label} className="glass rounded-xl p-3 text-center">
                  <p className="text-cyan-400 font-bold text-sm">{value}</p>
                  <p className="text-slate-500 text-xs">{sub}</p>
                </div>
              ))}
            </motion.div>
          </div>

          {/* RIGHT — Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
          >
            <AnimatePresence mode="wait">
              {result ? (
                <ResultsPanel key="results" result={result} originalUrl={preview} />
              ) : (
                <motion.div key="placeholder" initial={{ opacity: 0 }} animate={{ opacity: 0.6 }} exit={{ opacity: 0 }}
                  className="glass rounded-3xl p-10 flex flex-col items-center justify-center gap-4 text-center min-h-[320px]"
                >
                  <Brain size={40} className="text-slate-600" />
                  <div>
                    <p className="text-slate-400 font-medium">Results will appear here</p>
                    <p className="text-slate-600 text-sm mt-1">Upload an image and click Analyse Scan</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
