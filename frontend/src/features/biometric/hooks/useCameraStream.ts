/**
 * Hook to manage a getUserMedia video stream.
 *
 * Returns a ref to attach to a <video> element and controls to start/stop
 * the camera.  Automatically cleans up tracks on unmount.
 */

import { useRef, useCallback, useEffect, useState } from "react";

export type CameraFacing = "user" | "environment";

export function useCameraStream(facing: CameraFacing = "user") {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsActive(true);
    } catch (err: any) {
      setError(err.message || "Camera access denied.");
      setIsActive(false);
    }
  }, [facing]);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  }, []);

  // Stop camera on unmount.
  useEffect(() => stop, [stop]);

  return { videoRef, isActive, error, start, stop };
}
