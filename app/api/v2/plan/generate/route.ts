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
    const body = await req.json()
    const {
      user_id,
      full_name,
      age,
      occupation,
      monthly_income,
      monthly_expenses,
      current_savings,
      risk_appetite,
      investment_horizon,
      goals,
      retirement_age,
    } = body

    if (!user_id || !monthly_income) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const monthly_investment = Math.max(0, monthly_income - monthly_expenses)
    const years_to_invest = Math.max(1, (retirement_age || 60) - (age || 20))

    const prompt = `You are FinWise Teen, an expert AI financial advisor for young Indians. Generate a comprehensive, personalised investment plan.

User Profile:
- Name: ${full_name}, Age: ${age}
- Occupation: ${occupation}
- Monthly Income: ₹${monthly_income}, Monthly Expenses: ₹${monthly_expenses}
- Available to Invest: ₹${monthly_investment}/month
- Current Savings: ₹${current_savings}
- Risk Appetite: ${risk_appetite}
- Investment Horizon: ${investment_horizon} years
- Goals: ${goals}
- Target Retirement Age: ${retirement_age}

Respond ONLY with a valid JSON object (no markdown, no code fences) in this exact structure:
{
  "monthly_investment": <number>,
  "allocation": [
    {
      "name": "<asset class name>",
      "percentage": <number 0-100>,
      "monthly_amount": <number>,
      "expected_return": <number annual % as decimal e.g. 0.12>,
      "risk_level": "<Low|Medium|High>",
      "instruments": ["<specific fund/instrument 1>", "<specific fund/instrument 2>"],
      "rationale": "<why this asset for this user>"
    }
  ],
  "reasoning": "<2-3 sentence overall AI reasoning for this portfolio>",
  "emergency_fund": {
    "recommended_amount": <number>,
    "months_covered": <number>,
    "current_coverage": <number>
  },
  "retirement_projection": {
    "monthly_investment": <number>,
    "years": <number>,
    "projected_corpus": <number>,
    "inflation_adjusted_corpus": <number>
  },
  "badges": ["<badge name if earned, e.g. Emergency Expert, High Flyer, Smart Saver>"]
}

Rules:
- Allocation percentages must sum to 100
- Use Indian context: ELSS, PPF, NPS, SGBs, REITs, direct equity via Zerodha/Groww, etc.
- Tailor aggressiveness to risk appetite (${risk_appetite})
- Include 4-8 asset classes
- Badge criteria: "Emergency Expert" if emergency fund >= 6 months, "High Flyer" if equity > 60%, "Smart Saver" if savings rate > 30%`

    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-pro' })
    const result = await model.generateContent(prompt)
    const text = result.response.text().trim()

    // Strip markdown code fences if present
    const jsonText = text.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '').trim()
    const planData = JSON.parse(jsonText)

    // Persist to Supabase
    const { data: savedPlan, error: dbError } = await supabase
      .from('investment_plans')
      .insert({
        user_id,
        monthly_investment: planData.monthly_investment,
        allocation: planData.allocation,
        reasoning: planData.reasoning,
        emergency_fund: planData.emergency_fund,
        retirement_projection: planData.retirement_projection,
        badges: planData.badges,
        created_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (dbError) {
      console.error('Supabase insert error:', dbError)
      // Return plan even if save fails
      return NextResponse.json(planData)
    }

    return NextResponse.json({ ...planData, id: savedPlan.id })
  } catch (err) {
    console.error('Plan generation error:', err)
    return NextResponse.json(
      { error: 'Failed to generate plan. Please try again.' },
      { status: 500 }
    )
  }
}
