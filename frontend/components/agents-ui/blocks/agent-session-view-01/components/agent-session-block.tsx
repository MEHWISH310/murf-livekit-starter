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
      return 'ring-blue-500 bg-blue-50';
    case 'thinking':
      return 'ring-amber-500 bg-amber-50';
    case 'speaking':
      return 'ring-lime-600 bg-lime-100 scale-105';
    default:
      return 'ring-border bg-muted';
  }
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
    if (initialMessage && !hasSentInitial.current && session.isConnected) {
      hasSentInitial.current = true;
      send(initialMessage);
    }
  }, [initialMessage, session.isConnected, send]);

  const label = getStateLabel(agentState, session.isConnected);
  const stateColor = getStateColor(agentState);

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
        {/* Left: avatar + state */}
        <div className="border-border bg-card flex flex-1 flex-col items-center justify-center rounded-xl border p-6">
          <div
            className={cn(
              'mb-6 flex size-40 items-center justify-center rounded-full text-6xl ring-4 transition-all duration-300',
              stateColor
            )}
          >
            🌾
          </div>
          <p className="text-foreground text-lg font-semibold">{label}</p>
          <p className="text-muted-foreground mt-1 max-w-xs text-center text-sm">
            Ask about crops, weather, pests, mandi prices, or schemes.
          </p>
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