'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, TrendingUp, RefreshCw, Zap } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v2'

import BlueprintGrid from '@/components/ui/BlueprintGrid'

export default function WidgetPage() {
  const [pulse, setPulse] = useState<any>(null)
  
  useEffect(() => {
    const fetchPulse = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/market/pulse`)
        if (res.ok) {

          const data = await res.json()
          setPulse(data)
        }
      } catch (e) {}
    }
    fetchPulse()
    const interval = setInterval(fetchPulse, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-transparent p-4 flex items-center justify-center">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-[300px] h-[300px] glass-card p-6 relative overflow-hidden flex flex-col justify-between border-2 border-indigo-500/30 shadow-2xl shadow-indigo-500/20"
      >
        <div className="absolute inset-0 z-0 opacity-20">
          <BlueprintGrid />
        </div>

        <div className="relative z-10 flex flex-col h-full">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-[10px] uppercase tracking-widest font-bold text-indigo-400">FinWise Live Widget</h1>
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>

          <div className="space-y-6 flex-1 flex flex-col justify-center">
             <div>
                <p className="text-[8px] text-slate-500 uppercase font-bold tracking-tighter mb-1">NIFTY 50</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold font-mono tracking-tighter">
                    {pulse?.find((p: any) => p.symbol === 'NIFTY')?.price?.toLocaleString() || '23,456'}
                  </span>
                  <span className="text-xs text-emerald-400 font-bold">
                    +{pulse?.find((p: any) => p.symbol === 'NIFTY')?.change_percent?.toFixed(2) || '0.45'}%
                  </span>
                </div>
             </div>

             <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                   <div className="text-[8px] text-slate-500 font-bold mb-1">FITNESS</div>
                   <div className="text-lg font-bold text-indigo-400">84%</div>
                </div>
                <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                   <div className="text-[8px] text-slate-500 font-bold mb-1">RUNWAY</div>
                   <div className="text-lg font-bold text-rose-400">12 Mo</div>
                </div>
             </div>
          </div>

          <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[9px] text-slate-500">
             <span className="flex items-center gap-1 font-bold">
               <Shield size={10} className="text-indigo-400" /> AI SECURE
             </span>
             <span className="font-mono">v2.0.4-LITE</span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
