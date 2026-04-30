import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { GoogleGenerativeAI } from '@google/generative-ai'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!)

export async function POST(req: NextRequest) {
  try {
    const { message, user_id, plan_context } = await req.json()

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    // Fetch user's plan for context if user_id provided and no context given
    let planSummary = plan_context || ''
    if (!planSummary && user_id) {
      const { data: plan } = await supabase
        .from('investment_plans')
        .select('monthly_investment, allocation, reasoning, retirement_projection, badges')
        .eq('user_id', user_id)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()

      if (plan) {
        planSummary = `
User's Investment Plan:
- Monthly Investment: ₹${plan.monthly_investment}
- Allocation: ${JSON.stringify(plan.allocation?.map((a: { name: string; percentage: number }) => `${a.name}: ${a.percentage}%`))}
- Reasoning: ${plan.reasoning}
- Projected Corpus: ₹${plan.retirement_projection?.projected_corpus?.toLocaleString('en-IN')}
- Badges earned: ${plan.badges?.join(', ') || 'None yet'}
        `.trim()
      }
    }

    const systemPrompt = `You are FinWise Genie, a friendly, expert financial advisor chatbot for FinWise Teen — an AI-powered financial planning app for young Indians.

${planSummary ? `You have access to the user's personalised investment plan:\n${planSummary}\n` : ''}

Your personality:
- Friendly, encouraging, and relatable for teenagers and young adults
- Knowledgeable about Indian financial markets, tax laws (80C, ELSS, NPS), and investment products
- Give specific, actionable advice — not vague generalities
- Use ₹ (rupees) for all amounts
- Keep answers concise (2-4 sentences) unless a detailed explanation is needed
- If asked about their plan specifically, reference the plan context above

Never recommend specific stocks for speculative trading. Always remind users this is educational advice, not SEBI-registered financial advice.`

    const model = genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      systemInstruction: systemPrompt,
    })

    const result = await model.generateContent(message)
    const reply = result.response.text()

    return NextResponse.json({ reply })
  } catch (err) {
    console.error('Chat error:', err)
    return NextResponse.json(
      { error: 'FinWise Genie is taking a short break. Please try again!' },
      { status: 500 }
    )
  }
}
