'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, CheckCircle, ChevronRight, GraduationCap, X } from 'lucide-react'

interface Quest {
  id: string
  title: string
  pill: string
  content: string[]
  quiz: {
    question: string
    options: string[]
    answer: number
  }
  reward: string
}

const quests: Quest[] = [
  {
    id: 'reits',
    title: 'What are REITs?',
    pill: 'Beginner',
    content: [
      "Real Estate Investment Trusts (REITs) are like mutual funds for property.",
      "Companies own big buildings (offices, malls) and collect rent.",
      "When you buy a REIT, you get a share of that rent as dividends!",
      "It's a way to 'own' real estate without buying a whole building."
    ],
    quiz: {
      question: "What is the main way you earn from a REIT?",
      options: ["Selling the bricks", "Monthly Rent Dividends", "Fixed Deposits"],
      answer: 1
    },
    reward: 'REIT Scout Badge'
  },
  {
    id: 'indexing',
    title: 'The Magic of Indexing',
    pill: 'Intermediate',
    content: [
      "An Index Fund tracks the top 50 companies in India (NIFTY 50).",
      "Instead of picking one winner, you bet on the entire Indian Economy.",
      "Statistically, index funds beat 90% of active fund managers over 10 years.",
      "It's low cost, automated, and the ultimate teen investment tool."
    ],
    quiz: {
      question: "What does the NIFTY 50 track?",
      options: ["The top 50 Indian stocks", "50 random startups", "The top 50 gold mines"],
      answer: 0
    },
    reward: 'Index Master Badge'
  }
]

export default function LearningQuest() {
  const [activeQuest, setActiveQuest] = useState<Quest | null>(null)
  const [step, setStep] = useState(0)
  const [showQuiz, setShowQuiz] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)

  const quest = activeQuest || quests[0]

  const handleNext = () => {
    if (step < quest.content.length - 1) {
      setStep(step + 1)
    } else {
      setShowQuiz(true)
    }
  }

  const handleQuizSubmit = (idx: number) => {
    setSelectedOption(idx)
    if (idx === quest.quiz.answer) {
      setTimeout(() => {
        setCompleted(true)
      }, 500)
    }
  }

  const closeQuest = () => {
     setActiveQuest(null)
     setStep(0)
     setShowQuiz(false)
     setCompleted(false)
     setSelectedOption(null)
  }

  return (
    <div className="flex flex-col h-full relative">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm">Learning Corner</h3>
        <GraduationCap size={14} className="text-violet-400" />
      </div>

      <div className="space-y-4 flex-1">
        {quests.map(q => (
           <button
             key={q.id}
             onClick={() => setActiveQuest(q)}
             className="w-full p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-violet-500/50 transition-all text-left group"
           >
             <div className="flex justify-between items-start mb-2">
               <span className="text-[8px] uppercase tracking-widest font-bold px-2 py-0.5 rounded bg-violet-500/20 text-violet-400">
                 {q.pill}
               </span>
               <ChevronRight size={14} className="text-slate-600 group-hover:text-violet-400 transition-colors" />
             </div>
             <h4 className="text-xs font-bold text-slate-200 mb-1">{q.title}</h4>
             <p className="text-[10px] text-slate-500">Earn {q.reward}</p>
           </button>
        ))}
      </div>

      <AnimatePresence>
        {activeQuest && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md"
          >
            <motion.div 
              initial={{ y: 20, scale: 0.95 }}
              animate={{ y: 0, scale: 1 }}
              className="glass-card max-w-md w-full p-8 relative overflow-hidden"
            >
              <button 
                onClick={closeQuest}
                className="absolute top-4 right-4 text-slate-500 hover:text-white"
              >
                <X size={20} />
              </button>

              {!showQuiz && !completed && (
                <div className="space-y-6 pt-4 text-center">
                  <div className="w-16 h-16 bg-violet-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="text-violet-400" size={32} />
                  </div>
                  <h2 className="text-2xl font-bold">{quest.title}</h2>
                  <motion.p 
                    key={step}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-lg text-slate-300 leading-relaxed font-jakarta"
                  >
                    "{quest.content[step]}"
                  </motion.p>
                  
                  <div className="flex justify-center gap-1">
                    {quest.content.map((_, i) => (
                      <div key={i} className={`h-1 rounded-full transition-all ${i === step ? 'w-8 bg-violet-500' : 'w-2 bg-white/10'}`} />
                    ))}
                  </div>
                  
                  <button onClick={handleNext} className="btn-primary w-full py-4 text-lg">
                    {step === quest.content.length - 1 ? 'Take the Quiz!' : 'Next'}
                  </button>
                </div>
              )}

              {showQuiz && !completed && (
                <div className="space-y-6 pt-4">
                  <h2 className="text-xl font-bold text-center">Quick Check!</h2>
                  <p className="text-slate-300 text-center mb-8">{quest.quiz.question}</p>
                  
                  <div className="space-y-3">
                    {quest.quiz.options.map((opt, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleQuizSubmit(idx)}
                        className={`w-full p-4 rounded-2xl border text-left transition-all ${
                          selectedOption === idx 
                            ? (idx === quest.quiz.answer ? 'border-emerald-500 bg-emerald-500/10' : 'border-rose-500 bg-rose-500/10')
                            : 'border-white/10 bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <span className="text-sm font-medium">{opt}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {completed && (
                <div className="space-y-6 pt-4 text-center">
                  <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-emerald-500/50">
                    <CheckCircle className="text-emerald-400" size={40} />
                  </div>
                  <h2 className="text-3xl font-bold text-emerald-400 glow-text">Quest Complete!</h2>
                  <p className="text-slate-300 italic">"Knowledge is the best asset."</p>
                  
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/5 inline-block">
                    <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">UNLOCKED</p>
                    <p className="font-bold text-indigo-400">{quest.reward}</p>
                  </div>

                  <button onClick={closeQuest} className="btn-primary w-full py-4 bg-emerald-600 hover:bg-emerald-500">
                    Done
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
