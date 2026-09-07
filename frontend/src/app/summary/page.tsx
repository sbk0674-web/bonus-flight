'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { AdSlot } from '@/components/AdSlot'
import { BackButton } from '@/components/BackButton'
import { BrandHeader } from '@/components/BrandHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useSearchStore } from '@/stores/useSearchStore'
import type { LegSelection } from '@/types/award'

function LegSummary({ title, leg }: { title: string; leg: LegSelection }) {
  const availableClasses = [
    leg.flight.seats.economy > 0 && `일반석 ${leg.flight.seats.economy}석`,
    leg.flight.seats.business > 0 && `프레스티지석 ${leg.flight.seats.business}석`,
    leg.flight.seats.first > 0 && `일등석 ${leg.flight.seats.first}석`,
  ].filter(Boolean)
  const operatorNote =
    leg.flight.codeShare && leg.flight.operatorName ? `${leg.flight.operatorName} 운항` : null
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
          {leg.date} {leg.flight.flightNo} {leg.flight.depTime} 출발
        </p>
        <p className="text-muted-foreground">{availableClasses.join(' · ')}</p>
        {operatorNote && <p className="text-xs text-muted-foreground">{operatorNote}</p>}
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
        <BrandHeader />
        <BackButton />
        <h1 className="text-center text-lg font-medium">왕복 조회 결과</h1>
        <p className="rounded-md bg-muted p-3 text-xs text-muted-foreground">
          ⚠️ 하루 1회 업데이트되는 데이터라 실제로는 매진일 수 있습니다. 예약 전 대한항공
          사이트에서 반드시 다시 확인해주세요.
        </p>
        <LegSummary title="가는편" leg={outbound} />
        <LegSummary title="오는편" leg={inbound} />
        <Button onClick={handleRestart}>다시 조회</Button>
        <AdSlot />
      </div>
    </main>
  )
}
