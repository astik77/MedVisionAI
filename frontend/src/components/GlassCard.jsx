import { motion } from 'framer-motion'

export default function GlassCard({ children, className = '', glow = false, ...props }) {
  return (
    <motion.div
      className={`glass rounded-2xl p-6 ${glow ? 'glow-cyan' : ''} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
}
