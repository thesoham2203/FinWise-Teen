'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getMarketHistory } from '@/lib/market'

interface MicroSparklineProps {
  symbol?: string // New: Fetch live data if symbol is provided
  color?: string
  height?: number
  width?: number
  seed?: number 
}

export default function MicroSparkline({ 
  symbol,
  color = '#6366f1', 
  height = 30, 
  width = 80,
  seed = 0.5 
}: MicroSparklineProps) {
  const [points, setPoints] = useState<string>('')

  useEffect(() => {
    const fetchData = async () => {
      let data: { x: number; y: number }[] = []
      
      if (symbol) {
        const hist = await getMarketHistory(symbol)
        if (hist && hist.history.length > 0) {
          const prices = hist.history.map(p => p.close)
          const min = Math.min(...prices)
          const max = Math.max(...prices)
          const range = max - min || 1
          
          data = prices.map((p, i) => ({
            x: (i * width) / (prices.length - 1),
            y: height - ((p - min) / range) * height
          }))
        }
      }

      // Fallback to random walk if no live data
      if (data.length === 0) {
        const numPoints = 12
        let currentY = height / 2
        for (let i = 0; i < numPoints; i++) {
          const x = (i * width) / (numPoints - 1)
          const randomValue = Math.sin(i * seed * 10) * (height / 3) + (Math.random() - 0.5) * 10
          currentY = Math.max(0, Math.min(height, currentY + randomValue))
          data.push({ x, y: currentY })
        }
      }

      const path = data.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
      setPoints(path)
    }

    fetchData()
  }, [symbol, height, width, seed])


  return (
    <div className="relative overflow-visible" style={{ width, height }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id={`grad-${seed}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.2" />
            <stop offset="50%" stopColor={color} stopOpacity="1" />
            <stop offset="100%" stopColor={color} stopOpacity="0.4" />
          </linearGradient>
          <filter id={`glow-${seed}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        
        <motion.path
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeInOut" }}
          d={points}
          fill="none"
          stroke={`url(#grad-${seed})`}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter={`url(#glow-${seed})`}
        />
      </svg>
    </div>
  )
}
