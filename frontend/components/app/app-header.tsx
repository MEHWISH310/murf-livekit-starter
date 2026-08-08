import { LanguageToggle } from '@/components/app/language-toggle';

export function AppHeader() {
  return (
    <header className="bg-lime-900 text-white shrink-0">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-full bg-lime-600 text-xl">
            🌾
          </div>
          <div>
            <p className="text-sm leading-tight font-semibold">Kisan Sahay</p>
            <p className="text-xs leading-tight text-lime-300">Your Farming Voice Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <LanguageToggle />
          <span className="hidden rounded-full border border-lime-600 px-2 py-1 text-xs text-lime-300 sm:inline">
            Murf Falcon
          </span>
        </div>
      </div>
    </header>
  );
}