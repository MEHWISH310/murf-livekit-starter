'use client';
import { useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.5, ease: 'linear' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [isConnecting, setIsConnecting] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [micErrorMessage, setMicErrorMessage] = useState<string | null>(null);

  const handleStart = async (question?: string) => {
    setMicErrorMessage(null);
    setIsConnecting(true);
    if (question) setPendingQuestion(question);
    try {
      await start();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const isPermissionError =
        message.toLowerCase().includes('permission') ||
        message.toLowerCase().includes('notallowed') ||
        message.toLowerCase().includes('denied');
      setMicErrorMessage(
        isPermissionError
          ? 'Microphone access was blocked. Please allow microphone access in your browser settings and try again.'
          : 'Could not connect. Please check your internet connection and try again.'
      );
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <AnimatePresence mode="wait">
      {!isConnected && !isConnecting && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={() => handleStart()}
          onQuestionClick={(q: string) => handleStart(q)}
          errorMessage={micErrorMessage}
        />
      )}

      {!isConnected && isConnecting && (
        <motion.div
          key="connecting"
          {...VIEW_MOTION_PROPS}
          className="flex h-full w-full flex-col items-center justify-center gap-3"
        >
          <div className="size-12 animate-spin rounded-full border-4 border-lime-600 border-t-transparent" />
          <p className="text-foreground text-lg font-semibold">Connecting you to Kisan Sahay...</p>
          <p className="text-muted-foreground text-sm">Please wait a moment</p>
        </motion.div>
      )}

      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          initialMessage={pendingQuestion}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}