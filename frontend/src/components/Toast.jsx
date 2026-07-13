import { createContext, useContext, useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

// ── Context ─────────────────────────────────────────────────────
const ToastContext = createContext(null)

// ── Toast item config ────────────────────────────────────────────
const TOAST_CONFIG = {
  success: {
    icon: CheckCircle2,
    border: 'border-green-400/30',
    bg: 'bg-green-400/10',
    iconColor: 'text-green-400',
    bar: 'bg-green-400',
  },
  error: {
    icon: XCircle,
    border: 'border-red-400/30',
    bg: 'bg-red-400/10',
    iconColor: 'text-red-400',
    bar: 'bg-red-400',
  },
  info: {
    icon: Info,
    border: 'border-cyan-400/30',
    bg: 'bg-cyan-400/10',
    iconColor: 'text-cyan-400',
    bar: 'bg-cyan-400',
  },
}

// ── Single Toast ──────────────────────────────────────────────────
function Toast({ id, type = 'info', message, onDismiss }) {
  const cfg = TOAST_CONFIG[type] || TOAST_CONFIG.info
  const Icon = cfg.icon

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 60, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 60, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={`relative flex items-start gap-3 px-4 py-3 rounded-2xl border
        ${cfg.border} ${cfg.bg} backdrop-blur-md shadow-2xl w-80 overflow-hidden`}
    >
      {/* Progress bar */}
      <motion.div
        className={`absolute bottom-0 left-0 h-0.5 ${cfg.bar} opacity-60`}
        initial={{ width: '100%' }}
        animate={{ width: '0%' }}
        transition={{ duration: 4, ease: 'linear' }}
      />

      {/* Icon */}
      <Icon size={18} className={`flex-shrink-0 mt-0.5 ${cfg.iconColor}`} />

      {/* Message */}
      <p className="flex-1 text-sm text-slate-200 leading-snug">{message}</p>

      {/* Dismiss */}
      <button
        onClick={() => onDismiss(id)}
        className="flex-shrink-0 text-slate-500 hover:text-slate-300 transition-colors"
      >
        <X size={14} />
      </button>
    </motion.div>
  )
}

// ── Toast Container ───────────────────────────────────────────────
export function ToastContainer() {
  const ctx = useContext(ToastContext)
  if (!ctx) return null

  return (
    <div className="fixed top-20 right-4 z-[9999] flex flex-col gap-3 pointer-events-none">
      <AnimatePresence mode="sync">
        {ctx.toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <Toast {...t} onDismiss={ctx.dismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  )
}

// ── Provider ─────────────────────────────────────────────────────
let _idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const timers = useRef({})

  const dismiss = useCallback((id) => {
    clearTimeout(timers.current[id])
    delete timers.current[id]
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const add = useCallback((type, message) => {
    const id = ++_idCounter
    setToasts((prev) => [...prev.slice(-4), { id, type, message }]) // max 5 toasts
    timers.current[id] = setTimeout(() => dismiss(id), 4000)
    return id
  }, [dismiss])

  const toast = {
    success: (msg) => add('success', msg),
    error:   (msg) => add('error', msg),
    info:    (msg) => add('info', msg),
  }

  return (
    <ToastContext.Provider value={{ toasts, dismiss, toast }}>
      {children}
    </ToastContext.Provider>
  )
}

// ── Hook ─────────────────────────────────────────────────────────
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx.toast
}
