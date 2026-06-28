export type MarketCode = 'TW' | 'CN' | 'HK' | 'US'

export const MARKET_LABELS: Record<MarketCode, string> = {
  TW: '台股',
  CN: '中國 A 股',
  HK: '港股',
  US: '美股',
}

export const MARKET_ORDER: MarketCode[] = ['TW', 'CN', 'HK', 'US']

export function marketLabel(market?: string): string {
  const code = String(market || '').toUpperCase() as MarketCode
  return MARKET_LABELS[code] || market || ''
}
