'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MarketData {
  nifty50: { value: number; change: number; changePercent: number }
  sensex: { value: number; change: number; changePercent: number }
  gold: { value: number; change: number; changePercent: number }
  bond10y: { value: number }
}

const formatNum = (n: number, decimals = 2) => n.toFixed(decimals)

function Ticker({ label, value, change, pct }: { label: string; value: string; change: number; pct: number }) {
  const up = change >= 0
  return (
    <div className="flex flex-col">
      <div className="text-xs text-slate-500 mb-0.5">{label}</div>
      <div className="font-semibold text-sm">{value}</div>
      <div className={`flex items-center gap-1 text-xs font-medium ${up ? 'text-emerald-400' : 'text-red-400'}`}>
        {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
        {up ? '+' : ''}{formatNum(change, 0)} ({up ? '+' : ''}{formatNum(pct)}%)
      </div>
    </div>
  )
}

export default function MarketPulse() {
  const [data, setData] = useState<MarketData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/market/pulse`)
        if (res.ok) {
          const d = await res.json()
          setData(d)
        }
      } catch {
        // fallback mock data
        setData({
          nifty50: { value: 22450.5, change: 123.4, changePercent: 0.55 },
          sensex: { value: 73891.2, change: 412.1, changePercent: 0.56 },
          gold: { value: 73200, change: -150, changePercent: -0.2 },
          bond10y: { value: 7.05 },
        })
      }
      setLoading(false)
    }
    fetchMarket()
    const interval = setInterval(fetchMarket, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4 }}
      className="glass-card p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">🌐 Live Market Pulse</h3>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-500">Live</span>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-12 bg-white/5 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <Ticker label="NIFTY 50" value={data.nifty50.value.toLocaleString('en-IN')} change={data.nifty50.change} pct={data.nifty50.changePercent} />
          <Ticker label="SENSEX" value={data.sensex.value.toLocaleString('en-IN')} change={data.sensex.change} pct={data.sensex.changePercent} />
          <Ticker label="Gold (₹/10g)" value={`₹${data.gold.value.toLocaleString('en-IN')}`} change={data.gold.change} pct={data.gold.changePercent} />
          <div className="flex flex-col">
            <div className="text-xs text-slate-500 mb-0.5">10Y Bond Yield</div>
            <div className="font-semibold text-sm">{data.bond10y.value}%</div>
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <Minus size={11} /> Government Security
            </div>
          </div>
        </div>
      ) : null}

      <div className="text-xs text-slate-600 mt-4">
        Data for educational purposes only. Prices may be delayed.
      </div>
    </motion.div>
  )
}
