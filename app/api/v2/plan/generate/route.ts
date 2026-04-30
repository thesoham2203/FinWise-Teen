import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { GoogleGenerativeAI } from '@google/generative-ai'

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
      investment_horizon_years,
      retirement_age,
      dream_job,
    } = body

    if (!user_id || !monthly_income) {
      return NextResponse.json({ error: 'Missing required fields: user_id and monthly_income are required' }, { status: 400 })
    }

    const monthly_investment = Math.max(0, monthly_income - (monthly_expenses || 0))
    const years_to_invest = Math.max(1, (retirement_age || 60) - (age || 20))

    const prompt = `You are FinWise Teen, an expert AI financial advisor for young Indians. Generate a comprehensive, personalised investment plan.

User Profile:
- Name: ${full_name}, Age: ${age}
- Occupation: ${occupation}
- Monthly Income: ₹${monthly_income}, Monthly Expenses: ₹${monthly_expenses}
- Available to Invest: ₹${monthly_investment}/month
- Current Savings: ₹${current_savings}
- Risk Appetite: ${risk_appetite}
- Investment Horizon: ${investment_horizon_years || years_to_invest} years
- Dream Job/Goals: ${dream_job || 'Not specified'}
- Target Retirement Age: ${retirement_age}

Respond ONLY with a valid JSON object (no markdown, no code fences, no explanation) in this exact structure:
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
  "badges": ["<badge name if earned>"]
}

Rules:
- Allocation percentages must sum to exactly 100
- Use Indian context: ELSS, PPF, NPS, SGBs, REITs, direct equity via Zerodha/Groww, etc.
- Tailor aggressiveness to risk appetite (${risk_appetite})
- Include 4-8 asset classes
- Badge criteria: "Emergency Expert" if emergency fund >= 6 months, "High Flyer" if equity > 60%, "Smart Saver" if savings rate > 30%
- Return ONLY raw JSON, nothing else`

    const model = genAI.getGenerativeModel({ model: 'gemini-2.5-pro' })
    const result = await model.generateContent(prompt)
    const text = result.response.text().trim()

    // Robustly strip any markdown code fences Gemini may add
    const jsonText = text
      .replace(/^```(?:json)?\s*/i, '')
      .replace(/\s*```$/, '')
      .trim()

    let planData: Record<string, unknown>
    try {
      planData = JSON.parse(jsonText)
    } catch {
      console.error('Gemini returned non-JSON:', text.substring(0, 500))
      return NextResponse.json(
        { error: 'AI returned an invalid response. Please try again.' },
        { status: 500 }
      )
    }

    // Validate key fields exist
    if (!planData.allocation || !Array.isArray(planData.allocation)) {
      return NextResponse.json(
        { error: 'AI response missing allocation data. Please try again.' },
        { status: 500 }
      )
    }

    // Persist to Supabase using service role key (bypasses RLS)
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    )

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
      })
      .select()
      .single()

    if (dbError) {
      console.error('Supabase insert error:', JSON.stringify(dbError))
      // Still return the plan so the client can cache it in localStorage
      // Dashboard will fall back to localStorage
      return NextResponse.json({ ...planData, _saved: false })
    }

    return NextResponse.json({ ...planData, id: savedPlan.id, _saved: true })
  } catch (err) {
    console.error('Plan generation error:', err)
    return NextResponse.json(
      { error: `Failed to generate plan: ${err instanceof Error ? err.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
