'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useSearchStore } from '@/stores/useSearchStore'
import type { LegSelection } from '@/types/award'

function LegSummary({ title, leg }: { title: string; leg: LegSelection }) {
  return (
    <div className="border rounded p-4">
      <p className="font-semibold">{title}</p>
      <p>{leg.dep} → {leg.dest}</p>
      <p>{leg.date} {leg.flight.flightNo} {leg.flight.depTime}→{leg.flight.arrTime}</p>
      <p>
        이코노미 {leg.flight.seats.economy} · 비즈니스 {leg.flight.seats.business} · 일등석 {leg.flight.seats.first}
      </p>
    </div>
  )
}

export default function SummaryPage() {
  const router = useRouter()
  const { outbound, inbound, reset } = useSearchStore()

  useEffect(() => {
    if (!outbound || !inbound) {
      router.replace('/')
    }
  }, [outbound, inbound, router])

  if (!outbound || !inbound) return null

  function handleRestart() {
    reset()
    router.push('/')
  }

  return (
    <main className="flex flex-col gap-4 p-8">
      <h1 className="text-xl font-bold">왕복 조회 결과</h1>
      <LegSummary title="가는편" leg={outbound} />
      <LegSummary title="오는편" leg={inbound} />
      <Button onClick={handleRestart}>다시 조회</Button>
    </main>
  )
}
