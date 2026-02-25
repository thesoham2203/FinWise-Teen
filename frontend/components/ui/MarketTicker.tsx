'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { getMarketPulse, MarketPulseData } from '@/lib/market'

export default function MarketTicker() {
  const [data, setData] = useState<MarketPulseData | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      const pulse = await getMarketPulse()
      if (pulse) setData(pulse)
    }
    
    fetchData()
    const interval = setInterval(fetchData, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [])

  const tickerItems = data ? [
    { symbol: 'NIFTY 50', value: data.nifty50.value.toLocaleString('en-IN'), change: `${data.nifty50.changePercent > 0 ? '+' : ''}${data.nifty50.changePercent}%`, isUp: data.nifty50.changePercent >= 0 },
    { symbol: 'SENSEX', value: data.sensex.value.toLocaleString('en-IN'), change: `${data.sensex.changePercent > 0 ? '+' : ''}${data.sensex.changePercent}%`, isUp: data.sensex.changePercent >= 0 },
    { symbol: 'GOLD (10G)', value: data.gold.value.toLocaleString('en-IN'), change: `${data.gold.changePercent > 0 ? '+' : ''}${data.gold.changePercent}%`, isUp: data.gold.changePercent >= 0 },
    { symbol: '10Y BOND', value: `${data.bond10y.value}%`, change: '0.00%', isUp: true },
    { symbol: 'RELIANCE', value: '2,945', change: '+1.45%', isUp: true },
    { symbol: 'HDFC BANK', value: '1,422', change: '-0.65%', isUp: false },
  ] : [
    { symbol: 'NIFTY 50', value: 'Loading...', change: '...', isUp: true },
    { symbol: 'SENSEX', value: 'Loading...', change: '...', isUp: true },
  ]

  // Triple the data to ensure seamless scrolling
  const scrollData = [...tickerItems, ...tickerItems, ...tickerItems]

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[60] h-10 bg-slate-950/60 backdrop-blur-md border-t border-white/5 flex items-center overflow-hidden pointer-events-none select-none shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
      {/* Neon Top Border Glow */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
      
      <motion.div
        animate={{
          x: [0, -1200], 
        }}
        transition={{
          duration: 35,
          repeat: Infinity,
          ease: 'linear',
        }}
        className="flex items-center gap-12 whitespace-nowrap px-6"
      >
        {scrollData.map((item, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{item.symbol}</span>
            <span className="text-sm font-medium text-white/90 font-mono">{item.value}</span>
            <span className={`flex items-center gap-0.5 text-xs font-bold ${item.isUp ? 'text-emerald-400 glow-text' : 'text-rose-400 glow-text'}`}>
              {item.isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {item.change}
            </span>
          </div>
        ))}
      </motion.div>
    </div>
  )
}

