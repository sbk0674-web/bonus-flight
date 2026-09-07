export type MonthOption = {
  value: string
  label: string
}

// 안드로이드 크롬 등 일부 모바일 브라우저가 <input type="month">을 제대로
// 지원하지 않아서(빈 칸으로 보임) 직접 만든 목록으로 Select를 채운다.
export function getNextMonthOptions(fromMonth?: string, count = 12): MonthOption[] {
  const start = fromMonth ? new Date(`${fromMonth}-01T00:00:00`) : new Date()
  const options: MonthOption[] = []
  for (let i = 0; i < count; i += 1) {
    const d = new Date(start.getFullYear(), start.getMonth() + i, 1)
    const year = d.getFullYear()
    const month = d.getMonth() + 1
    const value = `${year}-${String(month).padStart(2, '0')}`
    options.push({ value, label: `${year}년 ${month}월` })
  }
  return options
}
