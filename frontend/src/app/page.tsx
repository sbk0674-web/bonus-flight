'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/useSearchStore'

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
    <main className="flex flex-col items-center gap-4 p-8">
      <h1 className="text-xl font-bold">출발지 선택</h1>
      <select
        className="border rounded p-2"
        value={dep}
        onChange={(e) => setDep(e.target.value)}
      >
        <option value="">국내공항 선택</option>
        {DOMESTIC_AIRPORTS.map((a) => (
          <option key={a.code} value={a.code}>
            {a.name} ({a.code})
          </option>
        ))}
      </select>
      <input
        type="month"
        className="border rounded p-2"
        value={month}
        onChange={(e) => setMonth(e.target.value)}
      />
      <Button disabled={!canSearch} onClick={handleSearch}>
        조회
      </Button>
    </main>
  )
}
