import { NextResponse } from 'next/server'

async function fetchYahooQuote(symbol: string) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`
  const res = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
    next: { revalidate: 60 },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${symbol}`)
  const json = await res.json()
  const result = json?.chart?.result?.[0]
  if (!result) throw new Error(`No data for ${symbol}`)
  const meta = result.meta
  const prev: number = meta.previousClose ?? meta.chartPreviousClose ?? meta.regularMarketPrice
  const curr: number = meta.regularMarketPrice
  const change = curr - prev
  const changePercent = parseFloat(((change / prev) * 100).toFixed(2))
  return { value: parseFloat(curr.toFixed(2)), change: parseFloat(change.toFixed(2)), changePercent }
}

export async function GET() {
  const [niftyResult, sensexResult, goldResult, usdInrResult] = await Promise.allSettled([
    fetchYahooQuote('^NSEI'),    // NIFTY 50
    fetchYahooQuote('^BSESN'),   // BSE SENSEX
    fetchYahooQuote('GC=F'),     // Gold futures (USD/troy oz)
    fetchYahooQuote('INR=X'),    // USD → INR rate
  ])

  const nifty50 = niftyResult.status === 'fulfilled'
    ? niftyResult.value
    : { value: 0, change: 0, changePercent: 0 }

  const sensex = sensexResult.status === 'fulfilled'
    ? sensexResult.value
    : { value: 0, change: 0, changePercent: 0 }

  let gold = { value: 0, change: 0, changePercent: 0 }
  if (goldResult.status === 'fulfilled' && usdInrResult.status === 'fulfilled') {
    const usdToInr = usdInrResult.value.value
    // 1 troy oz = 31.1035 g → price per 10g = (usd_per_oz * inr_per_usd) / 3.11035
    const goldUsd = goldResult.value.value
    const prevGoldUsd = goldUsd - goldResult.value.change
    const goldInr10g = (goldUsd * usdToInr) / 3.11035
    const prevGoldInr10g = (prevGoldUsd * usdToInr) / 3.11035
    const goldChange = goldInr10g - prevGoldInr10g
    gold = {
      value: parseFloat(goldInr10g.toFixed(2)),
      change: parseFloat(goldChange.toFixed(2)),
      changePercent: parseFloat(((goldChange / prevGoldInr10g) * 100).toFixed(2)),
    }
  }

  return NextResponse.json({
    nifty50,
    sensex,
    gold,
    bond10y: { value: 6.85 }, // 10Y India Govt Bond yield (approx; no reliable free source)
    source: 'yahoo_finance',
    timestamp: new Date().toISOString(),
  })
}
