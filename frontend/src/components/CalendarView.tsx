'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { CalendarDay, FlightOption } from '@/types/award'

type Props = {
  days: CalendarDay[]
  onSelectFlight: (date: string, flight: FlightOption) => void
}

export function CalendarView({ days, onSelectFlight }: Props) {
  if (days.length === 0) {
    return <p className="text-sm text-muted-foreground">이 달에는 좌석이 있는 날짜가 없습니다.</p>
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-3">
      {days.map((day) => (
        <Card key={day.date}>
          <CardHeader>
            <CardTitle className="text-sm">{day.date}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {day.flights.map((flight) => {
              const availableClasses = [
                flight.seats.economy > 0 && '이코노미',
                flight.seats.business > 0 && '비즈니스',
                flight.seats.first > 0 && '일등석',
              ].filter(Boolean)
              return (
                <Button
                  key={`${flight.flightNo}-${flight.depTime}`}
                  variant="outline"
                  className="h-auto w-full justify-start whitespace-normal py-2 text-left text-sm"
                  onClick={() => onSelectFlight(day.date, flight)}
                >
                  {flight.flightNo} {flight.depTime} 출발 | {availableClasses.join(' · ')} 가능
                </Button>
              )
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
