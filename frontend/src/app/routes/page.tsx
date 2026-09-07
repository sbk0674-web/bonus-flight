'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { BackButton } from '@/components/BackButton'
import { BrandHeader } from '@/components/BrandHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { fetchRoutes } from '@/lib/api'
import { getNextMonthOptions } from '@/lib/month-options'
import { useSearchStore } from '@/stores/useSearchStore'
import type { RouteOption } from '@/types/award'

function RoutesPageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const leg = params.get('leg') === 'inbound' ? 'inbound' : 'outbound'
  const { dep, month, outbound, setPendingDest, setReturnMonth } = useSearchStore()
  const [routeList, setRouteList] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedReturnMonth, setSelectedReturnMonth] = useState('')

  useEffect(() => {
    if (leg === 'inbound') {
      // 오는편은 노선 선택 없이 출발지로 고정, 리턴 월 선택 후 캘린더로 이동
      return
    }
    if (!dep || !month) {
      router.replace('/')
      return
    }
    setLoading(true)
    setError(null)
    fetchRoutes(dep, month)
      .then(setRouteList)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [dep, month, leg, outbound, router])

  function handleSelect(dest: string) {
    setPendingDest(dest)
    router.push('/calendar?leg=outbound')
  }

  function handleReturnMonthConfirm() {
    if (!selectedReturnMonth) return
    setReturnMonth(selectedReturnMonth)
    router.push('/calendar?leg=inbound')
  }

  if (leg === 'inbound') {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-2 bg-background p-6">
        <BrandHeader />
        <div className="w-full max-w-sm">
          <BackButton />
        </div>
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle className="text-lg">오는편 - 돌아오는 월 선택</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Select value={selectedReturnMonth} onValueChange={(value) => setSelectedReturnMonth(value as string)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="돌아오는 월 선택" />
              </SelectTrigger>
              <SelectContent>
                {getNextMonthOptions(outbound?.date?.slice(0, 7)).map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button disabled={!selectedReturnMonth} onClick={handleReturnMonthConfirm}>
              조회
            </Button>
          </CardContent>
        </Card>
      </main>
    )
  }

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-2 bg-background p-6">
        <BrandHeader />
        <div className="w-full max-w-sm">
          <BackButton />
        </div>
        <p className="text-center text-sm text-muted-foreground">
          해당 공항, 선택하신 월에 가능한 노선을 찾고 있습니다...
          <br />
          (최대 1분 정도 걸릴 수 있습니다)
        </p>
      </main>
    )
  }
  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-2 bg-background p-6">
        <BrandHeader />
        <div className="w-full max-w-sm">
          <BackButton />
        </div>
        <p className="text-destructive">{error}</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-2 bg-background p-6">
      <BrandHeader />
      <div className="w-full max-w-sm">
        <BackButton />
      </div>
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-lg">갈 수 있는 노선</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {routeList.length === 0 && (
            <p className="text-sm text-muted-foreground">취항 노선이 없습니다.</p>
          )}
          {routeList.map((r) => (
            <Button
              key={r.dest}
              variant="outline"
              className="w-full justify-start"
              onClick={() => handleSelect(r.dest)}
            >
              {r.destName} ({r.dest})
            </Button>
          ))}
        </CardContent>
      </Card>
    </main>
  )
}

export default function RoutesPage() {
  return (
    <Suspense fallback={<p className="p-8">불러오는 중...</p>}>
      <RoutesPageInner />
    </Suspense>
  )
}
