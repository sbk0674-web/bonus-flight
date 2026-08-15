'use client'

import type { CalendarDay, FlightOption } from '@/types/award'

type Props = {
  days: CalendarDay[]
  onSelectFlight: (date: string, flight: FlightOption) => void
}

export function CalendarView({ days, onSelectFlight }: Props) {
  if (days.length === 0) {
    return <p>이 달에는 좌석이 있는 날짜가 없습니다.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {days.map((day) => (
        <div key={day.date} className="border rounded p-3">
          <p className="font-semibold">{day.date}</p>
          <ul className="flex flex-col gap-1 mt-2">
            {day.flights.map((flight) => (
              <li key={flight.flightNo}>
                <button
                  className="border rounded p-2 w-full text-left text-sm"
                  onClick={() => onSelectFlight(day.date, flight)}
                >
                  {flight.flightNo} {flight.depTime}→{flight.arrTime} | 이코노미 {flight.seats.economy} · 비즈니스 {flight.seats.business} · 일등석 {flight.seats.first}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
