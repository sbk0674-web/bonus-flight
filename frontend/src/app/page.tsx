'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { fetchSettingsStatus } from '@/lib/api'
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
  const [configured, setConfigured] = useState<boolean | null>(null)

  useEffect(() => {
    fetchSettingsStatus()
      .then((status) => setConfigured(status.configured))
      .catch(() => setConfigured(null))
  }, [])

  const canSearch = dep !== '' && month !== ''

  function handleSearch() {
    setDeparture(dep, month)
    router.push('/routes')
  }

  return (
    <main className="flex flex-col items-center gap-4 p-8">
      <h1 className="text-xl font-bold">출발지 선택</h1>
      {configured === false && (
        <p className="text-sm text-red-600">
          대한항공 계정이 설정되지 않았습니다.{' '}
          <Link href="/settings" className="underline">
            설정 화면으로 이동
          </Link>
        </p>
      )}
      <Link href="/settings" className="text-sm text-gray-500 underline self-end">
        계정 설정
      </Link>
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
