import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, AlertTriangle } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-grid flex flex-col items-center justify-center px-4">
      {/* Ambient glow */}
      <div className="fixed top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-red-500/5 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center space-y-8 max-w-md"
      >
        {/* Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.2 }}
          className="flex justify-center"
        >
          <div className="p-5 rounded-3xl bg-red-400/10 border border-red-400/20">
            <AlertTriangle size={40} className="text-red-400" />
          </div>
        </motion.div>

        {/* 404 glitch number */}
        <div className="relative">
          <motion.h1
            className="text-[9rem] leading-none font-black text-white/5 select-none"
            aria-hidden="true"
          >
            404
          </motion.h1>
          <motion.p
            className="absolute inset-0 flex items-center justify-center text-7xl font-black"
            style={{
              background: 'linear-gradient(135deg, #22d3ee, #a855f7)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
            animate={{ opacity: [1, 0.7, 1], x: [0, -2, 2, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          >
            404
          </motion.p>
        </div>

        {/* Message */}
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Page Not Found</h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        {/* CTA */}
        <motion.div whileTap={{ scale: 0.97 }}>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm
              bg-gradient-to-r from-cyan-500 to-cyan-400 text-obsidian-950
              hover:from-cyan-400 hover:to-cyan-300 transition-all duration-200 shadow-lg
              shadow-cyan-500/25 hover:shadow-cyan-500/40"
          >
            <Home size={16} />
            Back to Dashboard
          </Link>
        </motion.div>
      </motion.div>
    </div>
  )
}
