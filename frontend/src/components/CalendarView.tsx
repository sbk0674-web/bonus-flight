'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { CalendarDay, FlightOption } from '@/types/award'

type Props = {
  days: CalendarDay[]
  onSelectFlight: (date: string, flight: FlightOption) => void
}

function hasAvailableSeats(flight: FlightOption): boolean {
  return flight.seats.economy > 0 || flight.seats.business > 0 || flight.seats.first > 0
}

export function CalendarView({ days, onSelectFlight }: Props) {
  const availableDays = days
    .map((day) => ({ ...day, flights: day.flights.filter(hasAvailableSeats) }))
    .filter((day) => day.flights.length > 0)

  if (availableDays.length === 0) {
    return <p className="text-sm text-muted-foreground">이 달에는 좌석이 있는 날짜가 없습니다.</p>
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      {availableDays.map((day) => (
        <Card key={day.date}>
          <CardHeader>
            <CardTitle className="text-sm">{day.date}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {day.flights.map((flight) => {
              const availableClasses = [
                flight.seats.economy > 0 && `일반석 ${flight.seats.economy}석`,
                flight.seats.business > 0 && `프레스티지석 ${flight.seats.business}석`,
                flight.seats.first > 0 && `일등석 ${flight.seats.first}석`,
              ].filter(Boolean)
              const operatorNote =
                flight.codeShare && flight.operatorName ? ` · ${flight.operatorName} 운항` : ''
              return (
                <Button
                  key={`${flight.flightNo}-${flight.depTime}`}
                  variant="outline"
                  className="h-auto w-full justify-start whitespace-normal py-2 text-left text-sm"
                  onClick={() => onSelectFlight(day.date, flight)}
                >
                  {flight.flightNo} {flight.depTime} 출발 | {availableClasses.join(' · ')}
                  {operatorNote}
                </Button>
              )
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
