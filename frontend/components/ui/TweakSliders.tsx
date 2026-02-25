'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Sliders, RefreshCw, AlertCircle } from 'lucide-react'

interface AllocationItem {
  name: string
  percentage: number
  expectedReturn?: string
  [key: string]: any
}

interface TweakSlidersProps {
  initialAllocation: AllocationItem[]
  onUpdate: (newAllocation: AllocationItem[]) => void
}

export default function TweakSliders({ initialAllocation, onUpdate }: TweakSlidersProps) {
  const [allocation, setAllocation] = useState<AllocationItem[]>(initialAllocation)
  const [total, setTotal] = useState(100)

  useEffect(() => {
    const sum = allocation.reduce((acc, curr) => acc + curr.percentage, 0)
    setTotal(Math.round(sum))
  }, [allocation])

  const handleSliderChange = (idx: number, newVal: number) => {
    const updated = [...allocation]
    updated[idx].percentage = newVal
    setAllocation(updated)
    onUpdate(updated)
  }

  const reset = () => {
    setAllocation(initialAllocation)
    onUpdate(initialAllocation)
  }

  const isInvalid = total !== 100

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">Fine-Tune Weights</h3>
        <button 
          onClick={reset}
          className="text-[10px] uppercase font-bold text-slate-500 hover:text-white flex items-center gap-1 transition-colors"
        >
          <RefreshCw size={10} /> Reset to AI
        </button>
      </div>

      <div className="space-y-4 max-h-[250px] overflow-y-auto pr-2 custom-scrollbar">
        {allocation.map((item, i) => (
          <div key={item.name} className="space-y-1">
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-slate-400">{item.name}</span>
              <span className="font-mono font-bold text-indigo-400">{item.percentage}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={item.percentage}
              onChange={(e) => handleSliderChange(i, parseInt(e.target.value))}
              className="w-full h-1 bg-white/5 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        ))}
      </div>

      <div className={`mt-4 p-3 rounded-xl border flex items-center justify-between ${isInvalid ? 'bg-rose-500/10 border-rose-500/20' : 'bg-emerald-500/10 border-emerald-500/20'}`}>
        <div className="flex items-center gap-2">
          {isInvalid ? (
            <AlertCircle size={14} className="text-rose-500" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
          )}
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">
            Total Weight: {total}%
          </span>
        </div>
        {isInvalid && (
          <span className="text-[10px] text-rose-400 font-bold">Must equal 100%</span>
        )}
      </div>
    </div>
  )
}
