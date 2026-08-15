'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CalendarView } from '@/components/CalendarView'
import { fetchCalendar } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { CalendarDay, FlightOption } from '@/types/award'

function CalendarPageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const leg = params.get('leg') === 'inbound' ? 'inbound' : 'outbound'
  const store = useSearchStore()
  const [days, setDays] = useState<CalendarDay[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const dep = leg === 'outbound' ? store.dep : store.outbound?.dest ?? null
  const dest = leg === 'outbound' ? store.pendingDest : store.outbound?.dep ?? null
  const month = leg === 'outbound' ? store.month : store.outbound ? store.returnMonth : null

  useEffect(() => {
    if (!dep || !dest || !month) {
      router.replace('/')
      return
    }
    setLoading(true)
    setError(null)
    fetchCalendar(dep, dest, month)
      .then(setDays)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [dep, dest, month, router])

  function handleSelectFlight(date: string, flight: FlightOption) {
    if (!dep || !dest || !month) return
    const legSelection = { dep, dest, month, date, flight }
    if (leg === 'outbound') {
      store.setOutbound(legSelection)
      router.push('/routes?leg=inbound')
    } else {
      store.setInbound(legSelection)
      router.push('/summary')
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-6">
        <p className="text-sm text-muted-foreground">
          좌석 조회 중... (수 초~수십 초 걸릴 수 있습니다)
        </p>
      </main>
    )
  }
  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-6">
        <p className="text-destructive">{error}</p>
      </main>
    )
  }

  // 오는편은 가는편 출발일보다 이른 날짜를 선택할 수 없도록 필터링한다
  const visibleDays =
    leg === 'inbound' && store.outbound
      ? days.filter((day) => day.date >= store.outbound!.date)
      : days

  return (
    <main className="flex min-h-screen flex-col items-center gap-4 bg-background p-6">
      <h1 className="text-lg font-medium">{leg === 'outbound' ? '가는편' : '오는편'} 선택</h1>
      <p className="w-full max-w-md rounded-md bg-muted p-3 text-xs text-muted-foreground">
        ⚠️ 하루 1회 업데이트되는 데이터입니다. 실시간 현황이 아니므로 실제 예약 가능 여부는
        대한항공 사이트에서 한 번 더 확인해주세요.
      </p>
      <CalendarView days={visibleDays} onSelectFlight={handleSelectFlight} />
    </main>
  )
}

export default function CalendarPage() {
  return (
    <Suspense fallback={<p className="p-8">불러오는 중...</p>}>
      <CalendarPageInner />
    </Suspense>
  )
}
