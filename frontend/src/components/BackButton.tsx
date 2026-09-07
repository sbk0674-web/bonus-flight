'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export function BackButton() {
  const router = useRouter()
  return (
    <Button variant="ghost" className="self-start" onClick={() => router.back()}>
      ← 뒤로
    </Button>
  )
}
