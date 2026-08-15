'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
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
    <main className="flex flex-col items-center gap-4 p-8">
      <h1 className="text-xl font-bold">대한항공 계정 설정</h1>
      <p className="text-sm text-gray-500">
        좌석 조회는 이 계정으로 대한항공에 로그인해서 진행됩니다. 로컬 백엔드 서버에만 저장되며 대한항공 외 다른 곳으로는 전송되지 않습니다.
      </p>
      {currentId && (
        <p className="text-sm text-gray-500">현재 설정된 아이디: {currentId}</p>
      )}
      <input
        type="text"
        placeholder="SKYPASS 아이디"
        className="border rounded p-2 w-64"
        value={koreanairId}
        onChange={(e) => setKoreanairId(e.target.value)}
      />
      <input
        type="password"
        placeholder="비밀번호"
        className="border rounded p-2 w-64"
        value={koreanairPw}
        onChange={(e) => setKoreanairPw(e.target.value)}
      />
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <Button disabled={!canSave || saving} onClick={handleSave}>
        {saving ? '저장 중...' : '저장'}
      </Button>
    </main>
  )
}
