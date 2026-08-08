'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  useAgent,
  useChat,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { AppHeader } from '@/components/app/app-header';
import { cn } from '@/lib/shadcn/utils';

const QUICK_TOPICS = [
  'Wheat sowing time?',
  "Today's mandi price?",
  'Leaf spots on crop',
  'Govt schemes for me',
];

function getStateLabel(agentState: string | undefined, isConnected: boolean): string {
  if (!isConnected) return 'Call ended';
  switch (agentState) {
    case 'connecting':
    case 'initializing':
      return 'Connecting you to Kisan Sahay...';
    case 'listening':
      return 'Listening to you...';
    case 'thinking':
      return 'Kisan Sahay is thinking...';
    case 'speaking':
      return 'Kisan Sahay is answering...';
    default:
      return 'Connected';
  }
}

function getStateColor(agentState: string | undefined): string {
  switch (agentState) {
    case 'listening':
      return 'text-blue-700 bg-blue-50 border-blue-200';
    case 'thinking':
      return 'text-amber-700 bg-amber-50 border-amber-200';
    case 'speaking':
      return 'text-lime-700 bg-lime-100 border-lime-300';
    default:
      return 'text-muted-foreground bg-muted border-border';
  }
}

function getAvatarRing(agentState: string | undefined): string {
  switch (agentState) {
    case 'listening':
      return 'ring-blue-400 bg-blue-50';
    case 'thinking':
      return 'ring-amber-400 bg-amber-50';
    case 'speaking':
      return 'ring-lime-500 bg-lime-100 scale-105';
    default:
      return 'ring-border bg-muted';
  }
}

function getPingColor(agentState: string | undefined): string {
  switch (agentState) {
    case 'listening':
      return 'bg-blue-300';
    case 'speaking':
      return 'bg-lime-300';
    default:
      return '';
  }
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0');
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${m}:${s}`;
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
  initialMessage?: string | null;
}

export function AgentSessionView_01({
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  preConnectMessage,
  isPreConnectBufferEnabled,
  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  initialMessage,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();
  const { send } = useChat();
  const hasSentInitial = useRef(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Wait for the agent to actually be present in the room (agentState is
    // only defined once the agent participant has joined) — sending right
    // when the local participant connects is too early and the agent
    // never sees the message.
    if (initialMessage && !hasSentInitial.current && session.isConnected && agentState) {
      hasSentInitial.current = true;
      send(initialMessage);
    }
  }, [initialMessage, session.isConnected, agentState, send]);

  // Call duration timer
  useEffect(() => {
    if (!session.isConnected) return;
    const start = Date.now();
    setElapsed(0);
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [session.isConnected]);

  const label = getStateLabel(agentState, session.isConnected);
  const stateColor = getStateColor(agentState);

  const handleQuickTopic = (topic: string) => {
    if (session.isConnected) send(topic);
  };

  return (
    <section
      ref={ref}
      className={cn(
        'bg-background relative z-10 flex h-full w-full flex-col overflow-hidden',
        className
      )}
      {...props}
    >
      <AppHeader />

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 overflow-hidden p-4 md:flex-row">
        {/* Left: avatar + state + quick topics */}
        <div className="border-border bg-card relative flex flex-1 flex-col items-center justify-center gap-6 overflow-hidden rounded-xl border p-6">
          {/* status + timer chips */}
          <div className="absolute top-4 left-4 flex items-center gap-2">
            <span
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium',
                stateColor
              )}
            >
              <span className="size-1.5 animate-pulse rounded-full bg-current" />
              {agentState ?? 'connected'}
            </span>
          </div>
          {session.isConnected && (
            <div className="absolute top-4 right-4">
              <span className="border-border bg-background/80 text-muted-foreground rounded-full border px-3 py-1 font-mono text-xs">
                {formatDuration(elapsed)}
              </span>
            </div>
          )}

          <div className="relative flex items-center justify-center">
            {(agentState === 'listening' || agentState === 'speaking') && (
              <span
                className={cn(
                  'absolute inline-flex size-40 animate-ping rounded-full opacity-60 md:size-56',
                  getPingColor(agentState)
                )}
              />
            )}
            <div
              className={cn(
                'relative size-32 overflow-hidden rounded-full shadow-lg ring-4 transition-all duration-300 md:size-44',
                getAvatarRing(agentState)
              )}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/kisan-sahay-avatar-session.jpg"
                alt="Kisan Sahay"
                className="size-full object-cover"
              />
            </div>
            {agentState === 'thinking' && (
              <div className="absolute -bottom-2 flex gap-1">
                <span className="size-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.3s]" />
                <span className="size-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.15s]" />
                <span className="size-2 animate-bounce rounded-full bg-amber-500" />
              </div>
            )}
          </div>

          <div className="text-center">
            <p className="text-foreground text-lg font-semibold">{label}</p>
            <p className="text-muted-foreground mt-1 max-w-xs text-center text-sm">
              Ask about crops, weather, pests, mandi prices, or schemes.
            </p>
          </div>

          {/* Quick topics — send straight into the chat/voice session */}
          <div className="flex w-full max-w-md flex-wrap justify-center gap-2">
            {QUICK_TOPICS.map((topic) => (
              <button
                key={topic}
                type="button"
                onClick={() => handleQuickTopic(topic)}
                className="border-border bg-background hover:border-lime-600 hover:bg-lime-50 rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm transition-colors"
              >
                {topic}
              </button>
            ))}
          </div>
        </div>

        {/* Right: live transcript, always visible */}
        <div className="border-border bg-card flex w-full flex-col overflow-hidden rounded-xl border shadow-sm md:w-96">
          <div className="border-border bg-muted/30 flex items-center justify-between border-b px-4 py-3">
            <p className="text-xs font-semibold tracking-wide uppercase">Live Transcript</p>
            <span className="flex items-center gap-1 text-xs text-green-600">
              <span className="size-2 animate-pulse rounded-full bg-green-500" />
              Live
            </span>
          </div>
          <div ref={scrollAreaRef} className="flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center px-6 text-center">
                <p className="text-muted-foreground text-sm">
                  Your conversation will appear here as you talk.
                </p>
              </div>
            ) : (
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="[&_.is-user>div]:rounded-[18px] [&>div>div]:px-4 [&>div>div]:py-4"
              />
            )}
          </div>
        </div>
      </div>

      {/* Bottom controls */}
      <div className="border-border bg-background border-t px-4 py-3">
        <div className="mx-auto max-w-2xl">
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </div>
    </section>
  );
}