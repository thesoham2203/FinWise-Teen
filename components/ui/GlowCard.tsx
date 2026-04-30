import { motion } from 'framer-motion'
import { ReactNode } from 'react'
import BlueprintGrid from './BlueprintGrid'

interface GlowCardProps {
  children: ReactNode
  className?: string
  glowColor?: string
}

export default function GlowCard({ children, className = "p-6", glowColor = "rgba(99, 102, 241, 0.4)" }: GlowCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.01, translateY: -2 }}
      className={`glass-card relative group overflow-hidden ${className}`}
    >
      <BlueprintGrid />

      {/* Animated Border Glow */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: `radial-gradient(600px circle at var(--mouse-x, 0) var(--mouse-y, 0), ${glowColor}, transparent 40%)`
        }}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          e.currentTarget.style.setProperty("--mouse-x", `${x}px`);
          e.currentTarget.style.setProperty("--mouse-y", `${y}px`);
        }}
      />
      
      {/* Nested Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Decorative Corner Glow */}
      <div className="absolute -top-10 -right-10 w-20 h-20 bg-indigo-500/10 blur-3xl rounded-full" />
      <div className="absolute -bottom-10 -left-10 w-20 h-20 bg-violet-500/10 blur-3xl rounded-full" />
    </motion.div>
  )
}
