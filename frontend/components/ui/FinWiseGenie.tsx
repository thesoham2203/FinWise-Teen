'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, X, Send, Sparkles, Bot, User, ChevronDown } from 'lucide-react'
import BrandLogo from '@/components/BrandLogo'

interface Message {
  role: 'assistant' | 'user'
  content: string
}

export default function FinWiseGenie() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hi! I'm your FinWise Genie. 🧞‍♂️ Ask me anything about your investment plan, taxes, or compounding!" }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      // Get context from local storage if available
      const storedPlan = localStorage.getItem('finwise_plan')
      const context_plan = storedPlan ? JSON.parse(storedPlan) : null

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'demo_user',
          message: userMsg,
          context_plan
        })
      })

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Oops, I lost my connection to the magic lamp. Try again in a bit!" }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-[200]">
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, rotate: -45 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 45 }}
            onClick={() => setIsOpen(true)}
            className="w-14 h-14 rounded-full bg-indigo-600 hover:bg-indigo-500 shadow-xl shadow-indigo-600/30 flex items-center justify-center text-white border-2 border-white/20 relative group"
          >
            <Sparkles className="animate-pulse" size={24} />
            <div className="absolute -top-12 right-0 bg-white text-slate-900 text-[10px] font-bold px-3 py-1.5 rounded-xl whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity shadow-lg pointer-events-none">
              Ask Genie 🧞‍♂️
            </div>
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="w-[380px] h-[550px] bg-[#0F121D] border border-white/10 rounded-3xl shadow-2xl flex flex-col overflow-hidden relative"
          >
             {/* Gradient Background */}
             <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/10 to-transparent pointer-events-none" />

             {/* Header */}
             <div className="p-4 border-b border-white/5 flex items-center justify-between relative z-10 bg-white/5">
                <div className="flex items-center gap-2">
                   <div className="w-8 h-8 rounded-lg bg-indigo-600/20 flex items-center justify-center">
                     <BrandLogo size={18} />
                   </div>
                   <div>
                     <h4 className="text-sm font-bold">FinWise Genie</h4>
                     <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Always Online</span>
                     </div>
                   </div>
                </div>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-white/5 rounded-xl transition-colors text-slate-400 hover:text-white"
                >
                  <ChevronDown size={20} />
                </button>
             </div>

             {/* Messages */}
             <div className="flex-1 overflow-y-auto p-4 space-y-4 relative z-10 custom-scrollbar">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                      m.role === 'user' 
                        ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/20' 
                        : 'bg-white/5 text-slate-200 border border-white/10 rounded-tl-none font-jakarta'
                    }`}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {loading && (
                   <div className="flex justify-start">
                     <div className="bg-white/5 p-3 rounded-2xl rounded-tl-none border border-white/10 flex gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" />
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce delay-75" />
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce delay-150" />
                     </div>
                   </div>
                )}
                <div ref={chatEndRef} />
             </div>

             {/* Input */}
             <div className="p-4 border-t border-white/5 relative z-10">
                <div className="relative">
                  <input 
                    type="text" 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask about your SIP, LTCG tax..."
                    className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:border-indigo-500/50 transition-all font-jakarta"
                  />
                  <button 
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    className="absolute right-2 top-2 w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center text-white disabled:opacity-50 disabled:grayscale transition-all"
                  >
                    <Send size={16} />
                  </button>
                </div>
                <p className="text-[10px] text-center text-slate-500 mt-2 font-jakarta">
                  Powered by Gemini 1.5 Pro · Plan Aware
                </p>
             </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
