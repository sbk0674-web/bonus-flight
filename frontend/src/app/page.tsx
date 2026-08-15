'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useSearchStore } from '@/stores/useSearchStore'

const DOMESTIC_AIRPORTS = [
  { code: 'ICN', name: '인천' },
  { code: 'GMP', name: '김포' },
  { code: 'PUS', name: '부산(김해)' },
  { code: 'CJU', name: '제주' },
  { code: 'TAE', name: '대구' },
  { code: 'CJJ', name: '청주' },
  { code: 'KWJ', name: '광주' },
  { code: 'USN', name: '울산' },
  { code: 'RSU', name: '여수' },
  { code: 'KPO', name: '포항경주' },
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
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-lg">대한항공 마일리지 좌석 조회</CardTitle>
          <CardDescription>출발 공항과 월을 골라주세요</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            좌석 조회 버튼을 누르면 브라우저 창이 하나 열립니다. 그 창에서 직접 대한항공에
            로그인(네이버 등 소셜 로그인 포함)해주세요.
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
            <Input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
          </div>

          <Button disabled={!canSearch} onClick={handleSearch} className="mt-2">
            조회
          </Button>
        </CardContent>
      </Card>
    </main>
  )
}
