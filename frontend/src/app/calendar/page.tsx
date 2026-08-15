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
  const dest = leg === 'outbound' ? store.pendingDest : store.dep
  const month = leg === 'outbound' ? store.month : store.pendingDest ? store.month : null

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
      store.setPendingDest(dep) // 리턴 노선 화면에서 도착지가 원래 출발지로 고정되도록
      router.push('/routes?leg=inbound')
    } else {
      store.setInbound(legSelection)
      router.push('/summary')
    }
  }

  if (loading) return <p className="p-8">좌석 조회 중... (수 초~수십 초 걸릴 수 있습니다)</p>
  if (error) return <p className="p-8 text-red-600">{error}</p>

  return (
    <main className="flex flex-col gap-4 p-8">
      <h1 className="text-xl font-bold">{leg === 'outbound' ? '가는편' : '오는편'} 선택</h1>
      <CalendarView days={days} onSelectFlight={handleSelectFlight} />
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
