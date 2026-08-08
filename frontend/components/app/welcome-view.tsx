'use client';

import { Button } from '@/components/ui/button';
import { AppHeader } from '@/components/app/app-header';

const FEATURES = [
  { icon: '🌱', label: 'Crops & Sowing', desc: 'Sowing seasons and crop care advice' },
  { icon: '☁️', label: 'Weather Guidance', desc: 'General weather-related farming tips' },
  { icon: '💰', label: 'Mandi Prices', desc: 'Approximate mandi price trends' },
  { icon: '📋', label: 'Govt Schemes', desc: 'Awareness of farmer welfare schemes' },
];

const HOW_IT_WORKS = [
  { step: '1', text: 'Tap the button to start' },
  { step: '2', text: 'Allow microphone access when prompted' },
  { step: '3', text: 'Speak naturally, in Hindi, English, or a mix' },
  { step: '4', text: 'End the call anytime and start again' },
];

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  onQuestionClick: (question: string) => void;
  errorMessage?: string | null;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  errorMessage,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="flex h-full flex-col overflow-hidden">
      <AppHeader />
      <section className="farm-animated-bg relative flex flex-1 items-center overflow-hidden px-4 py-6">
        {/* decorative farm-colored polka dots */}
        <span className="floating-dot pointer-events-none absolute top-14 left-10 size-6 bg-lime-500 opacity-40 [animation-delay:0s]" />
        <span className="floating-dot pointer-events-none absolute top-1/3 right-20 size-10 bg-amber-500 opacity-35 [animation-delay:1.5s]" />
        <span className="floating-dot pointer-events-none absolute bottom-20 left-1/4 size-5 bg-yellow-600 opacity-40 [animation-delay:3s]" />
        <span className="floating-dot pointer-events-none absolute right-1/4 bottom-12 size-8 bg-green-700 opacity-30 [animation-delay:4.5s]" />
        <span className="floating-dot pointer-events-none absolute top-1/2 left-16 size-4 bg-amber-700 opacity-35 [animation-delay:2.2s]" />
        <span className="floating-dot pointer-events-none absolute top-20 right-1/3 size-7 bg-lime-600 opacity-30 [animation-delay:5s]" />

        <div className="relative mx-auto grid w-full max-w-6xl gap-8 lg:grid-cols-2 lg:items-center">
          {/* Left: intro + button + features */}
          <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
            <div className="border-lime-300 mb-4 size-28 overflow-hidden rounded-full border-4 bg-lime-50 shadow-lg">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/kisan-sahay-avatar-landing.jpg"
                alt="Kisan Sahay"
                className="size-full object-cover"
              />
            </div>
            <h1 className="text-foreground text-2xl font-bold lg:text-3xl">Kisan Sahay</h1>
            <p className="text-muted-foreground mt-2 max-w-md leading-6">
              Ask about crops, sowing seasons, weather, pest problems, mandi
              prices, or government schemes, just by talking.
            </p>

            {errorMessage && (
              <div className="mt-4 w-full max-w-md rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-left">
                <p className="text-sm font-semibold text-red-800">Microphone access needed</p>
                <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
              </div>
            )}

            <Button
              size="lg"
              onClick={onStartCall}
              className="mt-6 w-64 rounded-full bg-lime-700 font-mono text-xs font-bold tracking-wider text-white uppercase hover:bg-lime-800"
            >
              {startButtonText}
            </Button>

            <div className="mt-8 grid w-full max-w-md grid-cols-2 gap-3">
              {FEATURES.map((f) => (
                <div
                  key={f.label}
                  className="border-border bg-card/90 flex flex-col items-start gap-1 rounded-lg border px-3 py-3 text-left shadow-sm backdrop-blur-sm"
                >
                  <span className="text-xl">{f.icon}</span>
                  <span className="text-sm font-semibold">{f.label}</span>
                  <span className="text-muted-foreground text-xs leading-snug">{f.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: how it works */}
          <div className="border-border bg-card/90 w-full rounded-xl border p-8 shadow-sm backdrop-blur-sm">
            <p className="text-muted-foreground mb-6 text-sm font-semibold tracking-wide uppercase">
              How it works
            </p>
            <div className="flex flex-col gap-7">
              {HOW_IT_WORKS.map((item) => (
                <div key={item.step} className="flex items-center gap-5">
                  <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-lime-100 text-lg font-bold text-lime-800">
                    {item.step}
                  </span>
                  <p className="text-foreground text-lg">{item.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
      <div className="bg-lime-900 flex w-full items-center justify-center py-3">
        <p className="max-w-prose px-4 text-center text-xs leading-5 text-lime-200">
          Built for the 10 Days of Voice Agents challenge, VoiceForBharat Edition
        </p>
      </div>
    </div>
  );
};