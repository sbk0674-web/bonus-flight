'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { fetchRoutes } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { RouteOption } from '@/types/award'

function RoutesPageInner() {
  const router = useRouter()
  const params = useSearchParams()
  const leg = params.get('leg') === 'inbound' ? 'inbound' : 'outbound'
  const { dep, month, outbound, setPendingDest, setReturnMonth } = useSearchStore()
  const [routeList, setRouteList] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(true)
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
    fetchRoutes(dep, month)
      .then(setRouteList)
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
      <main className="flex flex-col gap-4 p-8">
        <h1 className="text-xl font-bold">오는편 - 돌아오는 월 선택</h1>
        <input
          type="month"
          className="border rounded p-2"
          value={selectedReturnMonth}
          onChange={(e) => setSelectedReturnMonth(e.target.value)}
        />
        <button
          className="border rounded p-2 w-fit disabled:opacity-50"
          disabled={!selectedReturnMonth}
          onClick={handleReturnMonthConfirm}
        >
          조회
        </button>
      </main>
    )
  }

  if (loading) return <p className="p-8">불러오는 중...</p>

  return (
    <main className="flex flex-col gap-2 p-8">
      <h1 className="text-xl font-bold">갈 수 있는 노선</h1>
      {routeList.length === 0 && <p>취항 노선이 없습니다.</p>}
      <ul className="flex flex-col gap-2">
        {routeList.map((r) => (
          <li key={r.dest}>
            <button
              className="border rounded p-2 w-full text-left"
              onClick={() => handleSelect(r.dest)}
            >
              {r.destName} ({r.dest})
            </button>
          </li>
        ))}
      </ul>
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
