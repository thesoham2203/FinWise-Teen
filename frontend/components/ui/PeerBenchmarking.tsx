'use client'

import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Users, MapPin, Calendar } from 'lucide-react'

interface PeerBenchmarkingProps {
  userDiversification: number
  userCity: string
  userAge: number
}

export default function PeerBenchmarking({ userDiversification, userCity, userAge }: PeerBenchmarkingProps) {
  
  const stats = useMemo(() => {
    return [
      {
        label: `Teens in ${userCity}`,
        userValue: userDiversification,
        peerValue: 3.2,
        icon: MapPin,
        color: 'text-blue-400'
      },
      {
        label: `Investors Aged ${userAge}-${userAge + 2}`,
        userValue: userDiversification,
        peerValue: 2.8,
        icon: Calendar,
        color: 'text-violet-400'
      }
    ]
  }, [userDiversification, userCity, userAge])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">How I Compare</h3>
        <Users size={14} className="text-indigo-400" />
      </div>

      <div className="space-y-6 flex-1">
        {stats.map((s, i) => {
          const isBetter = s.userValue >= s.peerValue
          const pctBetter = Math.round(((s.userValue - s.peerValue) / s.peerValue) * 100)
          
          return (
            <div key={i} className="space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <s.icon size={12} className={s.color} /> {s.label}
                </span>
                <span className={`font-bold ${isBetter ? 'text-emerald-400' : 'text-amber-400'}`}>
                   {isBetter ? 'TOP TIER' : 'AVERAGE'}
                </span>
              </div>
              
              <div className="relative h-2 bg-white/5 rounded-full overflow-hidden">
                {/* Peer Average Marker */}
                <div 
                  className="absolute top-0 bottom-0 w-0.5 bg-white/20 z-10" 
                  style={{ left: `${(s.peerValue / 6) * 100}%` }}
                />
                
                {/* User Bar */}
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(s.userValue / 6) * 100}%` }}
                  transition={{ duration: 1, delay: i * 0.2 }}
                  className={`h-full ${isBetter ? 'bg-emerald-500/40' : 'bg-amber-500/40'}`}
                />
              </div>
              
              <div className="flex justify-between text-[9px]">
                <span className="text-slate-500">Peer Avg: {s.peerValue} Assets</span>
                <span className={isBetter ? 'text-emerald-500' : 'text-slate-500'}>
                  {isBetter ? `+${pctBetter}% more diversified` : 'Keep exploring!'}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <p className="text-[9px] text-slate-500 leading-tight mt-4 bg-white/5 p-2 rounded-lg border border-white/5">
        Tip: Diversifying into <b>Gold</b> or <b>P2P Lending</b> could put you in the top 5% of your peer group.
      </p>
    </div>
  )
}
