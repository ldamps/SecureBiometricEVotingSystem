/**
 * Camera hook for biometric capture using react-native-vision-camera.
 *
 * Provides photo capture that returns raw pixel data via Skia for
 * feature extraction.
 */

import { useRef, useCallback, useEffect, useState } from "react";
import { Camera, useCameraDevice, useCameraPermission } from "react-native-vision-camera";
import { Skia } from "@shopify/react-native-skia";
import * as ImageManipulator from "expo-image-manipulator";
import * as FileSystem from "expo-file-system";
import { PixelBuffer } from "../services/feature-extraction.utils";

const TARGET_SIZE = 224;

export function useCamera() {
  const device = useCameraDevice("front");
  const { hasPermission, requestPermission } = useCameraPermission();
  const cameraRef = useRef<Camera>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

  const onInitialized = useCallback(() => setReady(true), []);

  /**
   * Capture a photo and return a 224x224 PixelBuffer.
   */
  const captureFrame = useCallback(async (): Promise<PixelBuffer | null> => {
    if (!cameraRef.current || !ready) return null;

    try {
      // Take photo
      const photo = await cameraRef.current.takePhoto({
        qualityPrioritization: "speed",
      });

      // Resize to 224x224
      const manipulated = await ImageManipulator.manipulateAsync(
        `file://${photo.path}`,
        [{ resize: { width: TARGET_SIZE, height: TARGET_SIZE } }],
        { format: ImageManipulator.SaveFormat.PNG },
      );

      // Read file as base64 and decode to pixels via Skia
      const base64 = await FileSystem.readAsStringAsync(manipulated.uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const skData = Skia.Data.fromBase64(base64);
      const image = Skia.Image.MakeImageFromEncoded(skData);

      if (!image) return null;

      const width = image.width();
      const height = image.height();

      // readPixels returns RGBA Uint8Array
      const pixels = image.readPixels(0, 0, {
        width,
        height,
        colorType: 4, // RGBA_8888
        alphaType: 1, // Opaque
      });

      if (!pixels) return null;

      return {
        data: new Uint8ClampedArray(pixels),
        width,
        height,
      };
    } catch {
      return null;
    }
  }, [ready]);

  return {
    cameraRef,
    device,
    hasPermission,
    ready,
    onInitialized,
    captureFrame,
  };
}
