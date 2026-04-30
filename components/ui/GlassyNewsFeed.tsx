'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Newspaper, ExternalLink, TrendingUp, TrendingDown, Clock } from 'lucide-react'

interface NewsItem {
  id: string
  title: string
  source: string
  time: string
  sentiment: 'positive' | 'negative' | 'neutral'
  url: string
}

const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'NIFTY 50 hits all-time high of 23,000+; Investors jubilant.',
    source: 'MoneyControl',
    time: '2 mins ago',
    sentiment: 'positive',
    url: '#'
  },
  {
    id: '2',
    title: 'Gold prices see slight correction after central bank announcement.',
    source: 'Economic Times',
    time: '15 mins ago',
    sentiment: 'neutral',
    url: '#'
  },
  {
    id: '3',
    title: 'Tech stocks face pressure as global inflation worries persist.',
    source: 'LiveMint',
    time: '45 mins ago',
    sentiment: 'negative',
    url: '#'
  },
  {
    id: '4',
    title: 'New SIP rules for 2024: What young investors need to know.',
    source: 'FinWise Daily',
    time: '1 hour ago',
    sentiment: 'positive',
    url: '#'
  }
]

export default function GlassyNewsFeed() {
  const [news, setNews] = useState<NewsItem[]>(mockNews)
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % news.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [news.length])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">FinWise News Feed</h3>
        <Newspaper size={14} className="text-emerald-400" />
      </div>

      <div className="flex-1 relative overflow-hidden bg-white/[0.02] border border-white/5 rounded-2xl p-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={news[index].id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-[8px] uppercase tracking-widest font-bold px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
                {news[index].source}
              </span>
              <div className="flex items-center gap-1 text-[8px] text-slate-500 font-bold uppercase">
                <Clock size={10} /> {news[index].time}
              </div>
            </div>

            <h4 className="text-sm font-bold leading-snug group cursor-pointer hover:text-indigo-400 transition-colors">
              {news[index].title}
            </h4>

            <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
              <div className="flex items-center gap-2">
                {news[index].sentiment === 'positive' ? (
                  <TrendingUp size={12} className="text-emerald-400" />
                ) : news[index].sentiment === 'negative' ? (
                  <TrendingDown size={12} className="text-rose-400" />
                ) : (
                  <div className="w-3 h-3 rounded-full bg-slate-500" />
                )}
                <span className={`text-[10px] font-bold uppercase ${
                  news[index].sentiment === 'positive' ? 'text-emerald-400' : 
                  news[index].sentiment === 'negative' ? 'text-rose-400' : 'text-slate-500'
                }`}>
                  {news[index].sentiment} SENTIMENT
                </span>
              </div>
              <a href={news[index].url} className="text-slate-500 hover:text-white transition-colors">
                <ExternalLink size={14} />
              </a>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="flex justify-center gap-1 mt-4">
        {news.map((_, i) => (
          <button 
            key={i} 
            onClick={() => setIndex(i)}
            className={`h-1 rounded-full transition-all ${i === index ? 'w-6 bg-indigo-500' : 'w-2 bg-white/10'}`} 
          />
        ))}
      </div>
    </div>
  )
}
