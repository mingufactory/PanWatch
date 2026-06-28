export interface MarketBadgeInfo {
  style: string
  label: string
}

export function getMarketBadge(market: string): MarketBadgeInfo {
  if (market === 'TW') return { style: 'bg-red-500/10 text-red-600', label: '台股' }
  if (market === 'HK') return { style: 'bg-orange-500/10 text-orange-600', label: '港股' }
  if (market === 'US') return { style: 'bg-green-500/10 text-green-600', label: '美股' }
  if (market === 'CN') return { style: 'bg-blue-500/10 text-blue-600', label: 'A股' }
  return { style: 'bg-slate-500/10 text-slate-600', label: market }
}
