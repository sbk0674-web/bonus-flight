export type SeatCounts = {
  economy: number
  business: number
  first: number
}

export type FlightOption = {
  flightNo: string
  depTime: string
  arrTime: string
  seats: SeatCounts
  operatorCode: string | null
  operatorName: string | null
  codeShare: boolean
}

export type CalendarDay = {
  date: string
  flights: FlightOption[]
}

export type RouteOption = {
  dest: string
  destName: string
}

export type LegSelection = {
  dep: string
  dest: string
  month: string
  date: string
  flight: FlightOption
}
