export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;
  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;
  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  // agent dispatch configuration
  agentName?: string;
  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Kisan Sahay',
  pageTitle: 'Kisan Sahay — Voice Assistant for Farmers',
  pageDescription:
    'A voice assistant that helps farmers with crops, weather, mandi prices, and government schemes, powered by Murf Falcon',
  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,
  logo: '/kisan-sahay-logo.svg',
  accent: '#4D7C0F',
  logoDark: '/kisan-sahay-logo-dark.svg',
  accentDark: '#84CC16',
  startButtonText: 'Talk to Kisan Sahay',
  audioVisualizerType: 'bar',
  audioVisualizerColor: '#4D7C0F',
  audioVisualizerColorDark: '#84CC16',
  audioVisualizerBarCount: 5,
  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,
  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};