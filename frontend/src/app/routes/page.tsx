'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { fetchRoutes } from '@/lib/api'
import { useSearchStore } from '@/stores/useSearchStore'
import type { RouteOption } from '@/types/award'

export default function RoutesPage() {
  const router = useRouter()
  const { dep, month, setPendingDest } = useSearchStore()
  const [routeList, setRouteList] = useState<RouteOption[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!dep || !month) {
      router.replace('/')
      return
    }
    fetchRoutes(dep, month)
      .then(setRouteList)
      .finally(() => setLoading(false))
  }, [dep, month, router])

  function handleSelect(dest: string) {
    setPendingDest(dest)
    router.push('/calendar?leg=outbound')
  }

  if (loading) return <p className="p-8">노선 불러오는 중...</p>

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
