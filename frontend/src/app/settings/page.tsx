'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { fetchSettingsStatus, saveSettings } from '@/lib/api'

export default function SettingsPage() {
  const router = useRouter()
  const [koreanairId, setKoreanairId] = useState('')
  const [koreanairPw, setKoreanairPw] = useState('')
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSettingsStatus()
      .then((status) => setCurrentId(status.koreanairId))
      .catch(() => {})
  }, [])

  const canSave = koreanairId !== '' && koreanairPw !== ''

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      await saveSettings(koreanairId, koreanairPw)
      router.push('/')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-lg">대한항공 계정 설정</CardTitle>
          <CardDescription>
            좌석 조회는 이 계정으로 대한항공에 로그인해서 진행됩니다. 로컬 백엔드 서버에만
            저장되며 대한항공 외 다른 곳으로는 전송되지 않습니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {currentId && (
            <p className="text-sm text-muted-foreground">현재 설정된 아이디: {currentId}</p>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">SKYPASS 아이디</label>
            <Input
              type="text"
              value={koreanairId}
              onChange={(e) => setKoreanairId(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">비밀번호</label>
            <Input
              type="password"
              value={koreanairPw}
              onChange={(e) => setKoreanairPw(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button disabled={!canSave || saving} onClick={handleSave} className="mt-2">
            {saving ? '저장 중...' : '저장'}
          </Button>
        </CardContent>
      </Card>
    </main>
  )
}
