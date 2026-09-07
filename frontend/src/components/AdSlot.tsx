'use client'

import { useEffect } from 'react'

const CLIENT_ID = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID
const SLOT_ID = process.env.NEXT_PUBLIC_ADSENSE_SLOT_ID

declare global {
  interface Window {
    adsbygoogle?: unknown[]
  }
}

// publisher ID(NEXT_PUBLIC_ADSENSE_CLIENT_ID)와 슬롯 ID(NEXT_PUBLIC_ADSENSE_SLOT_ID)를
// frontend/.env.local에 채우면 바로 실제 광고가 뜬다. 비어 있는 동안은 자리만 보여준다.
// (참고: 로컬호스트에서는 애드센스 정책상 실제 광고가 서빙되지 않는다 — 배포된
// 도메인에서만 뜬다.)
export function AdSlot() {
  const configured = Boolean(CLIENT_ID && SLOT_ID)

  useEffect(() => {
    if (!configured) return
    try {
      window.adsbygoogle = window.adsbygoogle || []
      window.adsbygoogle.push({})
    } catch {
      // 스크립트 로드 전 push 실패는 무시 (광고 표시 실패는 치명적이지 않음)
    }
  }, [configured])

  if (!configured) {
    return (
      <div className="flex w-full max-w-md items-center justify-center rounded-md border border-dashed border-[var(--border)] bg-muted/50 p-4 text-xs text-muted-foreground">
        광고 영역 (AdSense 미설정)
      </div>
    )
  }

  return (
    <ins
      className="adsbygoogle block w-full max-w-md"
      style={{ display: 'block' }}
      data-ad-client={CLIENT_ID}
      data-ad-slot={SLOT_ID}
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
  )
}
