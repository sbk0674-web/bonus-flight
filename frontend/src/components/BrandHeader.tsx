export function BrandHeader() {
  return (
    <header className="flex w-full flex-col items-center gap-1 pb-2">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--accent)] text-sm font-semibold tracking-widest text-[var(--accent)]">
          BF
        </span>
        <span className="text-sm font-medium tracking-[0.2em] text-primary">
          BONUS FLIGHT
        </span>
      </div>
      <span className="h-px w-16 bg-[var(--accent)]" />
    </header>
  )
}
