'use client';

import { Button } from '@/components/ui/button';
import { AppHeader } from '@/components/app/app-header';

const SUGGESTED_QUESTIONS = [
  'What is the right time to sow wheat?',
  "What is today's mandi price for wheat?",
  'My crop leaves have spots, what should I do?',
  'Are there any government schemes for farmers?',
];

const FEATURES = [
  { icon: '🌱', label: 'Crops & Sowing', desc: 'Sowing seasons and crop care advice' },
  { icon: '☁️', label: 'Weather Guidance', desc: 'General weather-related farming tips' },
  { icon: '💰', label: 'Mandi Prices', desc: 'Approximate mandi price trends' },
  { icon: '📋', label: 'Govt Schemes', desc: 'Awareness of farmer welfare schemes' },
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
  onQuestionClick,
  errorMessage,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="flex h-full flex-col overflow-y-auto">
      <AppHeader />
      <section className="bg-gradient-to-b from-lime-50 to-background flex-1 px-4 py-10">
        <div className="mx-auto grid w-full max-w-5xl gap-10 lg:grid-cols-2 lg:items-start">
          {/* Left column: intro + button + features */}
          <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
            <div className="mb-5 flex size-24 items-center justify-center rounded-full bg-lime-100 text-5xl shadow-sm">
              🌱
            </div>
            <h1 className="text-foreground text-2xl font-bold">Kisan Sahay</h1>
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

            <div className="mt-10 grid w-full max-w-md grid-cols-2 gap-3">
              {FEATURES.map((f) => (
                <div
                  key={f.label}
                  className="border-border bg-card flex flex-col items-start gap-1 rounded-lg border px-4 py-3 text-left shadow-sm"
                >
                  <span className="text-2xl">{f.icon}</span>
                  <span className="text-sm font-semibold">{f.label}</span>
                  <span className="text-muted-foreground text-xs">{f.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right column: suggested questions */}
          <div className="w-full">
            <p className="text-muted-foreground mb-3 text-xs font-semibold tracking-wide uppercase">
              Try asking
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTED_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => onQuestionClick(question)}
                  className="border-border bg-card hover:border-lime-600 hover:bg-lime-50 flex items-center gap-2 rounded-lg border px-4 py-3 text-left text-sm shadow-sm transition-colors"
                >
                  <span className="text-lime-700">?</span>
                  {question}
                </button>
              ))}
            </div>

            <div className="border-border bg-card mt-6 rounded-lg border p-4">
              <p className="text-sm font-semibold">How it works</p>
              <ol className="text-muted-foreground mt-2 list-inside list-decimal space-y-1 text-sm">
                <li>Tap the button or a suggested question</li>
                <li>Allow microphone access when prompted</li>
                <li>Speak naturally, in Hindi, English, or a mix</li>
                <li>End the call anytime and start again</li>
              </ol>
            </div>
          </div>
        </div>
      </section>
      <div className="flex w-full items-center justify-center py-3">
        <p className="text-muted-foreground max-w-prose px-4 text-center text-xs leading-5">
          Built for the 10 Days of Voice Agents challenge, VoiceForBharat Edition
        </p>
      </div>
    </div>
  );
};