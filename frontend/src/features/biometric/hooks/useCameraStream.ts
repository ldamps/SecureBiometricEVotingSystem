/**
 * Hook to manage a getUserMedia video stream.
 *
 * Returns a ref callback (not a ref object) to attach to a <video> element.
 * This ensures the stream is wired up the instant the element mounts,
 * eliminating the race condition where start() runs before the element exists.
 */

import { useRef, useCallback, useEffect, useState } from "react";

export type CameraFacing = "user" | "environment";

export function useCameraStream(facing: CameraFacing = "user") {
  const videoElRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Wire the stream to the video element and play. */
  const attachStream = useCallback(() => {
    const video = videoElRef.current;
    const stream = streamRef.current;
    if (video && stream) {
      video.srcObject = stream;
      video.play().catch(() => {});
    }
  }, []);

  /**
   * Ref callback — React calls this with the DOM node when the <video>
   * mounts and with null when it unmounts.  If the stream is already
   * available we attach immediately.
   */
  const videoRef = useCallback(
    (node: HTMLVideoElement | null) => {
      videoElRef.current = node;
      if (node) attachStream();
    },
    [attachStream],
  );

  const start = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      attachStream();
      setIsActive(true);
    } catch (err: any) {
      setError(err.message || "Camera access denied.");
      setIsActive(false);
    }
  }, [facing, attachStream]);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoElRef.current) {
      videoElRef.current.srcObject = null;
    }
    setIsActive(false);
  }, []);

  // When isActive flips to true the video element may have just rendered;
  // try attaching once more after a micro-tick.
  useEffect(() => {
    if (!isActive) return;
    const id = requestAnimationFrame(attachStream);
    return () => cancelAnimationFrame(id);
  }, [isActive, attachStream]);

  // Stop camera on unmount.
  useEffect(() => stop, [stop]);

  return { videoRef, videoElRef, isActive, error, start, stop };
}
