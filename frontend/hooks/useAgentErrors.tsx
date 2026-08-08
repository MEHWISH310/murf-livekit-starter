import { ReactNode, useEffect } from 'react';
import { toast as sonnerToast } from 'sonner';
import { RoomEvent } from 'livekit-client';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ToastProps {
  title: ReactNode;
  description: ReactNode;
}

function toastAlert(toast: ToastProps) {
  const title = toast.title;
  const description = toast.description;
  return sonnerToast.custom(
    (id) => (
      <Alert onClick={() => sonnerToast.dismiss(id)} className="bg-accent w-full md:w-[364px]">
        <WarningIcon weight="bold" />
        <AlertTitle>{title}</AlertTitle>
        {description ? <AlertDescription>{description}</AlertDescription> : null}
      </Alert>
    ),
    { duration: 15000 }
  );
}

export function useAgentErrors() {
  const agent = useAgent();
  const sessionContext = useSessionContext();
  const isConnected = sessionContext.isConnected;
  const end = sessionContext.end;
  const room = sessionContext.room;

  useEffect(() => {
    if (isConnected && agent.state === 'failed') {
      const reasons = agent.failureReasons;
      const reasonText = reasons.length > 0 ? reasons.join(', ') : 'Unknown error';
      toastAlert({
        title: 'Session ended',
        description: (
          <div>
            <p className="w-full">{reasonText}</p>
          </div>
        ),
      });
      end();
    }
  }, [agent, isConnected, end]);

  useEffect(() => {
    if (!room) {
      return;
    }

    function handleMediaDevicesError() {
      toastAlert({
        title: 'Microphone access needed',
        description: (
          <div>
            <p className="w-full">
              Kisan Sahay needs microphone access to hear you. Please allow microphone access in your browser and try again.
            </p>
          </div>
        ),
      });
    }

    room.on(RoomEvent.MediaDevicesError, handleMediaDevicesError);

    return function cleanup() {
      room.off(RoomEvent.MediaDevicesError, handleMediaDevicesError);
    };
  }, [room]);
}
