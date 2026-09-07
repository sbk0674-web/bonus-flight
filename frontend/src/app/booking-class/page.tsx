'use client'

import { useState } from 'react'
import { BackButton } from '@/components/BackButton'
import { BrandHeader } from '@/components/BrandHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function buildGoogleFlightsUrl(origin: string, destination: string, depDate: string, retDate: string): string {
  let query = `Flights to ${destination} from ${origin} on ${depDate}`
  if (retDate) {
    query += ` returning ${retDate}`
  }
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(query)}`
}

export default function CheapestFlightPage() {
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [depDate, setDepDate] = useState('')
  const [retDate, setRetDate] = useState('')

  const canSearch = origin.trim() !== '' && destination.trim() !== '' && depDate !== ''

  function handleSearch() {
    const url = buildGoogleFlightsUrl(origin.trim(), destination.trim(), depDate, retDate)
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-4 bg-background p-6">
      <BrandHeader />
      <div className="w-full max-w-sm">
        <BackButton />
      </div>
      <Card className="w-full max-w-sm border-[var(--border)] shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">최저가 항공권 찾기</CardTitle>
          <CardDescription>가는 곳, 오는 곳, 날짜만 입력하면 가장 싼 항공권을 바로 찾아드려요</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">출발지</label>
            <Input placeholder="예: 서울, 인천" value={origin} onChange={(e) => setOrigin(e.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">도착지</label>
            <Input placeholder="예: 도쿄, 오사카" value={destination} onChange={(e) => setDestination(e.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">가는 날</label>
            <Input type="date" value={depDate} onChange={(e) => setDepDate(e.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">오는 날 (편도면 비워두세요)</label>
            <Input type="date" value={retDate} onChange={(e) => setRetDate(e.target.value)} />
          </div>

          <Button disabled={!canSearch} onClick={handleSearch} className="mt-2">
            가장 싼 항공권 찾기
          </Button>

          <p className="text-center text-xs text-muted-foreground">
            버튼을 누르면 구글 항공권 검색 결과가 새 창으로 열려요.
          </p>
        </CardContent>
      </Card>
    </main>
  )
}
