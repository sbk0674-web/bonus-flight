import type { CalendarDay, RouteOption } from '@/types/award'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export async function fetchRoutes(dep: string, month: string): Promise<RouteOption[]> {
  const res = await fetch(`${API_BASE}/api/routes?dep=${dep}&month=${month}`)
  if (!res.ok) throw new Error('노선 조회 실패')
  const body = await res.json()
  return body.map((r: { dest: string; dest_name: string }) => ({
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
    const body = await res.json().catch(() => ({ detail: '조회 실패' }))
    throw new Error(body.detail ?? '조회 실패')
  }
  const body = await res.json()
  return body.map((day: { date: string; flights: Array<{ flight_no: string; dep_time: string; arr_time: string; seats: { economy: number; business: number; first: number } }> }) => ({
    date: day.date,
    flights: day.flights.map((f) => ({
      flightNo: f.flight_no,
      depTime: f.dep_time,
      arrTime: f.arr_time,
      seats: f.seats,
    })),
  }))
}
