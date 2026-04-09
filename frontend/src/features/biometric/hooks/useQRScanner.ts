/**
 * Hook that reads QR codes from the device camera using jsQR.
 *
 * Uses the rear camera (`environment`) and runs a requestAnimationFrame
 * loop that draws each video frame to an offscreen canvas, then passes
 * the ImageData to jsQR for decoding.
 */

import { useRef, useState, useCallback, useEffect } from "react";
import jsQR from "jsqr";
import { useCameraStream } from "./useCameraStream";

const SCAN_COOLDOWN_MS = 2000;

export function useQRScanner(onScan: (data: string) => void) {
  const camera = useCameraStream("environment");
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number>(0);
  const lastScanRef = useRef<number>(0);
  const [scanning, setScanning] = useState(false);

  const tick = useCallback(() => {
    const video = camera.videoElRef.current;
    if (!video || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(tick);
      return;
    }

    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) {
      rafRef.current = requestAnimationFrame(tick);
      return;
    }

    ctx.drawImage(video, 0, 0);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);

    if (code && code.data) {
      const now = Date.now();
      if (now - lastScanRef.current > SCAN_COOLDOWN_MS) {
        lastScanRef.current = now;
        onScan(code.data);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
  }, [camera.videoElRef, onScan]);

  const start = useCallback(async () => {
    await camera.start();
    setScanning(true);
  }, [camera]);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    camera.stop();
    setScanning(false);
  }, [camera]);

  // Start the decode loop when the camera becomes active.
  useEffect(() => {
    if (camera.isActive && scanning) {
      rafRef.current = requestAnimationFrame(tick);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [camera.isActive, scanning, tick]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return {
    videoRef: camera.videoRef,
    videoElRef: camera.videoElRef,
    isActive: camera.isActive,
    error: camera.error,
    scanning,
    start,
    stop,
  };
}
