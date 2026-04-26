/**
 * Ear recognition service.
 *
 * Extracts a 128-d feature descriptor from an ear image using
 * Histogram-of-Oriented-Gradients (HOG) style features:
 *   1. Capture a video frame at 224x224 grayscale
 *   2. Apply a 5x5 box-filter smoothing pass — this is critical for
 *      cross-session stability: without it, single-pixel jitter in the
 *      camera shifts gradient orientations enough to drift cells'
 *      histograms past the fuzzy extractor's RS error-correction budget
 *   3. Compute Sobel gradients
 *   4. Divide into a 4x4 cell grid (16 cells, each ~56x56 pixels). A
 *      coarser grid than HOG's textbook 8x8 because the ear isn't always
 *      framed at the same translation/scale, and small offsets must not
 *      shift features between cells
 *   5. Build a 9-bin gradient orientation histogram per cell, weighted
 *      by magnitude — yields 16 × 9 = 144 raw features
 *   6. Cell-wise L2-normalisation makes the descriptor invariant to
 *      illumination and contrast
 *   7. Project through a deterministic random matrix down to 128-d
 *   8. Final L2-normalisation so cosine similarity is meaningful
 *
 * Earlier versions of this file used global colour/intensity statistics
 * (per-channel means, intensity histograms, spatial block means). Those
 * features were dominated by ambient lighting and skin tone, so wrong
 * ears matched routinely within the same room. HOG features are tied to
 * silhouette and texture orientation, which is what genuinely
 * distinguishes one ear from another. The first HOG iteration used 8x8
 * cells with no smoothing and was too sensitive to framing — same ear,
 * slightly different head angle would shift features into adjacent
 * cells and overwhelm the RS correction budget. Smoothing + 4x4 cells
 * reins that in.
 */

import { FeatureExtractionResult } from "../models/biometric-feature.model";

const FEATURE_DIM = 128;
const RAW_DIM = 144;
const CELL_GRID = 4;
const ORIENTATION_BINS = 9;
const FRAME_SIZE = 224;
const SMOOTHING_KERNEL = 5;

/** Central region (in pixels) used for HOG. The 224×224 frame contains
 *  too much hair / neck / background; computing HOG over the whole frame
 *  lets a wrong ear from the same person in the same setting score
 *  almost identically to the enrolled ear because the descriptor is
 *  dominated by surrounding structure. Cropping to the inner region
 *  forces the descriptor to focus on the ear itself. */
const CROP_SIZE = 144;
const CROP_OFFSET = (FRAME_SIZE - CROP_SIZE) >> 1;

let projectionMatrix: Float32Array | null = null;
let canvas: HTMLCanvasElement | null = null;

/**
 * Deterministic PRNG (mulberry32) — produces identical sequences on
 * every device so enrollment and verification use the same projection.
 */
function mulberry32(seed: number): () => number {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildProjectionMatrix(): Float32Array {
  const rng = mulberry32(42);
  const matrix = new Float32Array(RAW_DIM * FEATURE_DIM);
  for (let i = 0; i < matrix.length; i += 2) {
    const u1 = rng();
    const u2 = rng();
    const r = Math.sqrt(-2 * Math.log(u1 || 1e-10));
    matrix[i] = r * Math.cos(2 * Math.PI * u2);
    if (i + 1 < matrix.length) {
      matrix[i + 1] = r * Math.sin(2 * Math.PI * u2);
    }
  }
  const scale = 1 / Math.sqrt(RAW_DIM);
  for (let i = 0; i < matrix.length; i++) matrix[i] *= scale;
  return matrix;
}

function project(source: Float32Array): Float32Array {
  if (!projectionMatrix) projectionMatrix = buildProjectionMatrix();
  const out = new Float32Array(FEATURE_DIM);
  for (let j = 0; j < FEATURE_DIM; j++) {
    let sum = 0;
    for (let i = 0; i < RAW_DIM; i++) {
      sum += source[i] * projectionMatrix[i * FEATURE_DIM + j];
    }
    out[j] = sum;
  }
  let norm = 0;
  for (let j = 0; j < FEATURE_DIM; j++) norm += out[j] * out[j];
  norm = Math.sqrt(norm) || 1;
  for (let j = 0; j < FEATURE_DIM; j++) out[j] /= norm;
  return out;
}

/**
 * Two-pass box blur — separable horizontal then vertical. O(width*height)
 * regardless of kernel size. Used to damp single-pixel noise before
 * gradient computation so HOG histograms are stable across captures.
 */
function boxBlur(
  src: Float32Array,
  width: number,
  height: number,
  kernel: number,
): Float32Array {
  const radius = (kernel - 1) >> 1;
  const horiz = new Float32Array(width * height);
  for (let y = 0; y < height; y++) {
    let sum = 0;
    for (let k = -radius; k <= radius; k++) {
      const x = Math.max(0, Math.min(width - 1, k));
      sum += src[y * width + x];
    }
    for (let x = 0; x < width; x++) {
      horiz[y * width + x] = sum / kernel;
      const xAdd = Math.min(width - 1, x + radius + 1);
      const xRem = Math.max(0, x - radius);
      sum += src[y * width + xAdd] - src[y * width + xRem];
    }
  }

  const out = new Float32Array(width * height);
  for (let x = 0; x < width; x++) {
    let sum = 0;
    for (let k = -radius; k <= radius; k++) {
      const y = Math.max(0, Math.min(height - 1, k));
      sum += horiz[y * width + x];
    }
    for (let y = 0; y < height; y++) {
      out[y * width + x] = sum / kernel;
      const yAdd = Math.min(height - 1, y + radius + 1);
      const yRem = Math.max(0, y - radius);
      sum += horiz[yAdd * width + x] - horiz[yRem * width + x];
    }
  }
  return out;
}

/**
 * Build HOG-style features: per-cell gradient orientation histograms
 * with L2 normalisation.
 *
 * Lighting affects gradient *magnitudes* but not *orientations*. By
 * normalising each cell's histogram to unit length, contrast and
 * exposure changes cancel out. What remains is the local edge geometry
 * — the curl of the helix, the antitragus, the lobe — which is what
 * actually identifies an ear.
 */
function extractRawFeatures(imageData: ImageData): Float32Array {
  const { data, width, height } = imageData;

  // Convert to grayscale in [0, 1].
  const grayRaw = new Float32Array(width * height);
  for (let i = 0; i < grayRaw.length; i++) {
    grayRaw[i] =
      (data[i * 4] * 0.299 +
        data[i * 4 + 1] * 0.587 +
        data[i * 4 + 2] * 0.114) /
      255;
  }

  // Box-filter smoothing — averages a SMOOTHING_KERNEL × SMOOTHING_KERNEL
  // window per pixel. Damps single-pixel noise so gradients are stable
  // across captures of the same ear.
  const gray = boxBlur(grayRaw, width, height, SMOOTHING_KERNEL);

  // Sobel gradients.
  const gradMag = new Float32Array(width * height);
  const gradOri = new Float32Array(width * height);
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const gx =
        -gray[(y - 1) * width + (x - 1)] +
        gray[(y - 1) * width + (x + 1)] +
        -2 * gray[y * width + (x - 1)] +
        2 * gray[y * width + (x + 1)] +
        -gray[(y + 1) * width + (x - 1)] +
        gray[(y + 1) * width + (x + 1)];
      const gy =
        -gray[(y - 1) * width + (x - 1)] -
        2 * gray[(y - 1) * width + x] -
        gray[(y - 1) * width + (x + 1)] +
        gray[(y + 1) * width + (x - 1)] +
        2 * gray[(y + 1) * width + x] +
        gray[(y + 1) * width + (x + 1)];
      gradMag[idx] = Math.sqrt(gx * gx + gy * gy);
      // Map [-π, π] → [0, π] (unsigned orientations: edges have the
      // same identity regardless of which side is brighter).
      let angle = Math.atan2(gy, gx);
      if (angle < 0) angle += Math.PI;
      gradOri[idx] = angle;
    }
  }

  // Per-cell HOG histograms — restricted to the central CROP_SIZE × CROP_SIZE
  // region of the frame so the descriptor reflects ear shape rather than
  // surrounding hair / neck / background, which otherwise dominate.
  const cellW = Math.floor(CROP_SIZE / CELL_GRID);
  const cellH = Math.floor(CROP_SIZE / CELL_GRID);
  const features = new Float32Array(RAW_DIM);
  let writeIdx = 0;

  for (let cy = 0; cy < CELL_GRID; cy++) {
    for (let cx = 0; cx < CELL_GRID; cx++) {
      const hist = new Float32Array(ORIENTATION_BINS);
      const yStart = CROP_OFFSET + cy * cellH;
      const yEnd =
        cy === CELL_GRID - 1
          ? CROP_OFFSET + CROP_SIZE
          : CROP_OFFSET + (cy + 1) * cellH;
      const xStart = CROP_OFFSET + cx * cellW;
      const xEnd =
        cx === CELL_GRID - 1
          ? CROP_OFFSET + CROP_SIZE
          : CROP_OFFSET + (cx + 1) * cellW;

      for (let y = yStart; y < yEnd; y++) {
        for (let x = xStart; x < xEnd; x++) {
          const idx = y * width + x;
          const mag = gradMag[idx];
          if (mag === 0) continue;
          const angle = gradOri[idx];
          const binFloat = (angle / Math.PI) * ORIENTATION_BINS;
          const bin = Math.min(ORIENTATION_BINS - 1, Math.floor(binFloat));
          hist[bin] += mag;
        }
      }

      // L2-normalise this cell's histogram — kills lighting / contrast.
      let norm = 0;
      for (let b = 0; b < ORIENTATION_BINS; b++) norm += hist[b] * hist[b];
      norm = Math.sqrt(norm) || 1;
      for (let b = 0; b < ORIENTATION_BINS; b++) {
        features[writeIdx++] = hist[b] / norm;
      }
    }
  }

  return features;
}

/**
 * Grab a video frame as 224x224 ImageData using a canvas.
 */
function captureFrame(video: HTMLVideoElement): ImageData {
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.width = FRAME_SIZE;
    canvas.height = FRAME_SIZE;
  }
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(video, 0, 0, FRAME_SIZE, FRAME_SIZE);
  return ctx.getImageData(0, 0, FRAME_SIZE, FRAME_SIZE);
}

// No async model loading required for the hand-crafted extractor.
export async function loadEarModel(): Promise<void> {
  projectionMatrix = buildProjectionMatrix();
}

export async function extractEarDescriptor(
  video: HTMLVideoElement,
): Promise<FeatureExtractionResult | null> {
  const imageData = captureFrame(video);
  const raw = extractRawFeatures(imageData);
  const descriptor = project(raw);
  return { descriptor, confidence: 1.0 };
}

export async function extractStableEarDescriptor(
  video: HTMLVideoElement,
  numSamples: number = 5,
  delayMs: number = 300,
): Promise<FeatureExtractionResult | null> {
  const descriptors: Float32Array[] = [];

  for (let i = 0; i < numSamples; i++) {
    const result = await extractEarDescriptor(video);
    if (result) descriptors.push(result.descriptor);
    if (i < numSamples - 1) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }

  if (descriptors.length === 0) return null;

  const averaged = new Float32Array(FEATURE_DIM);
  for (const d of descriptors) {
    for (let j = 0; j < FEATURE_DIM; j++) averaged[j] += d[j];
  }
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= descriptors.length;

  let norm = 0;
  for (let j = 0; j < FEATURE_DIM; j++) norm += averaged[j] * averaged[j];
  norm = Math.sqrt(norm) || 1;
  for (let j = 0; j < FEATURE_DIM; j++) averaged[j] /= norm;

  return { descriptor: averaged, confidence: 1.0 };
}
