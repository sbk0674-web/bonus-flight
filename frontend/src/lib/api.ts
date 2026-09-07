import type { CalendarDay, RouteOption } from '@/types/award'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

// 백엔드 Pydantic 응답 모델과 매칭되는 raw JSON 타입 (snake_case)
type RawRouteOption = {
  dest: string
  dest_name: string
}

type RawSeatCounts = {
  economy: number
  business: number
  first: number
}

type RawFlightOption = {
  flight_no: string
  dep_time: string
  arr_time: string
  seats: RawSeatCounts
  operator_code: string | null
  operator_name: string | null
  code_share: boolean
}

type RawCalendarDay = {
  date: string
  flights: RawFlightOption[]
}

type RawErrorBody = {
  detail?: string
}

export async function fetchRoutes(dep: string, month: string): Promise<RouteOption[]> {
  const res = await fetch(`${API_BASE}/api/routes?dep=${dep}&month=${month}`)
  if (!res.ok) throw new Error('노선 조회 실패')
  const body = (await res.json()) as unknown as RawRouteOption[]
  return body.map((r) => ({
    dest: r.dest,
    destName: r.dest_name,
  }))
}

export async function fetchCalendar(dep: string, dest: string, month: string): Promise<CalendarDay[]> {
  const res = await fetch(`${API_BASE}/api/calendar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dep, dest, month }),
  })
  if (!res.ok) {
    const errorBody = (await res.json().catch(() => ({ detail: '조회 실패' }))) as unknown as RawErrorBody
    throw new Error(errorBody.detail ?? '조회 실패')
  }
  const body = (await res.json()) as unknown as RawCalendarDay[]
  return body.map((day) => ({
    date: day.date,
    flights: day.flights.map((f) => ({
      flightNo: f.flight_no,
      depTime: f.dep_time,
      arrTime: f.arr_time,
      seats: f.seats,
      operatorCode: f.operator_code,
      operatorName: f.operator_name,
      codeShare: f.code_share,
    })),
  }))
}
