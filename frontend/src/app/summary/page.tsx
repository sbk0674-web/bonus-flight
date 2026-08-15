'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useSearchStore } from '@/stores/useSearchStore'
import type { LegSelection } from '@/types/award'

function LegSummary({ title, leg }: { title: string; leg: LegSelection }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 text-sm">
        <p>
          {leg.dep} → {leg.dest}
        </p>
        <p>
          {leg.date} {leg.flight.flightNo} {leg.flight.depTime}→{leg.flight.arrTime}
        </p>
        <p className="text-muted-foreground">
          이코노미 {leg.flight.seats.economy} · 비즈니스 {leg.flight.seats.business} · 일등석{' '}
          {leg.flight.seats.first}
        </p>
      </CardContent>
    </Card>
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
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6">
      <div className="flex w-full max-w-sm flex-col gap-4">
        <h1 className="text-center text-lg font-medium">왕복 조회 결과</h1>
        <LegSummary title="가는편" leg={outbound} />
        <LegSummary title="오는편" leg={inbound} />
        <Button onClick={handleRestart}>다시 조회</Button>
      </div>
    </main>
  )
}
