'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { AdSlot } from '@/components/AdSlot'
import { BrandHeader } from '@/components/BrandHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { getNextMonthOptions } from '@/lib/month-options'
import { useSearchStore } from '@/stores/useSearchStore'

const MONTH_OPTIONS = getNextMonthOptions()

// 대한항공 국제선(마일리지 보너스) 취항 국내공항만 포함. 대구/청주/광주/울산/여수/포항 등은
// 국내선만 운항해 국제선 목적지가 없으므로 제외 (getRouteByAirport API 실사 확인, 2026-08-16).
const DOMESTIC_AIRPORTS = [
  { code: 'ICN', name: '인천' },
  { code: 'GMP', name: '김포' },
  { code: 'PUS', name: '부산(김해)' },
  { code: 'CJU', name: '제주' },
]

export default function DeparturePage() {
  const router = useRouter()
  const setDeparture = useSearchStore((s) => s.setDeparture)
  const [dep, setDep] = useState('')
  const [month, setMonth] = useState('')

  const canSearch = dep !== '' && month !== ''

  function handleSearch() {
    setDeparture(dep, month)
    router.push('/routes')
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6">
      <BrandHeader />
      <Card className="w-full max-w-sm border-[var(--border)] shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">대한항공 마일리지 좌석 조회</CardTitle>
          <CardDescription>출발 공항과 월을 골라주세요</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            좌석 조회 버튼을 누르면 브라우저 창이 하나 열립니다. 그 창에서 직접 대한항공에
            로그인(네이버 등 소셜 로그인 포함)해주세요.
          </p>
          <p className="rounded-md bg-muted p-3 text-xs text-muted-foreground">
            ⚠️ 대한항공 좌석 데이터는 실시간이 아니라 <strong>하루 1회 업데이트</strong>됩니다.
            실제 예약 가능 여부는 대한항공 사이트에서 한 번 더 확인해주세요.
          </p>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">출발 공항</label>
            <Select value={dep} onValueChange={(value) => setDep(value as string)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="국내공항 선택" />
              </SelectTrigger>
              <SelectContent>
                {DOMESTIC_AIRPORTS.map((a) => (
                  <SelectItem key={a.code} value={a.code}>
                    {a.name} ({a.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">출발월</label>
            <Select value={month} onValueChange={(value) => setMonth(value as string)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="출발월 선택" />
              </SelectTrigger>
              <SelectContent>
                {MONTH_OPTIONS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button disabled={!canSearch} onClick={handleSearch} className="mt-2">
            조회
          </Button>
          <a
            href="https://www.koreanair.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-center text-xs text-muted-foreground underline underline-offset-2"
          >
            대한항공 홈페이지 바로가기
          </a>
          <button
            type="button"
            onClick={() => router.push('/booking-class')}
            className="text-center text-xs text-muted-foreground underline underline-offset-2"
          >
            최저가 항공권 찾기
          </button>
        </CardContent>
      </Card>
      <AdSlot />
    </main>
  )
}
