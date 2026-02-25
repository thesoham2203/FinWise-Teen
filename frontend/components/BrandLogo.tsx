'use client'

import { motion } from 'framer-motion'

export default function BrandLogo({ size = 32, className = "" }: { size?: number, className?: string }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: '100%', height: '100%' }}
      >
        <defs>
          <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Inner Circle / Coin Base */}
        <circle 
          cx="50" 
          cy="50" 
          r="40" 
          stroke="url(#logo-grad)" 
          strokeWidth="4" 
          strokeDasharray="10 5"
          className="opacity-20"
        />

        {/* Abstract "F" + Rising Line */}
        <motion.path
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeInOut" }}
          d="M30 70 L30 30 L60 30 M30 50 L55 50 M60 70 L75 40 L90 55"
          stroke="url(#logo-grad)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#glow)"
        />

        {/* Glowing Dot at the end of the line */}
        <motion.circle
          initial={{ scale: 0 }}
          animate={{ scale: [0, 1.2, 1] }}
          transition={{ delay: 1.2, duration: 0.5 }}
          cx="90" 
          cy="55" 
          r="5" 
          fill="#8b5cf6" 
          className="glow-primary"
        />
      </svg>
    </div>
  )
}
