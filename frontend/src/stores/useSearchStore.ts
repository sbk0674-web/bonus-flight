import { create } from 'zustand'
import type { LegSelection } from '@/types/award'

type SearchState = {
  dep: string | null
  month: string | null
  outbound: LegSelection | null
  inbound: LegSelection | null
  setDeparture: (dep: string, month: string) => void
  setOutbound: (leg: LegSelection) => void
  setInbound: (leg: LegSelection) => void
  reset: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  dep: null,
  month: null,
  outbound: null,
  inbound: null,
  setDeparture: (dep, month) => set({ dep, month }),
  setOutbound: (leg) => set({ outbound: leg }),
  setInbound: (leg) => set({ inbound: leg }),
  reset: () => set({ dep: null, month: null, outbound: null, inbound: null }),
}))
