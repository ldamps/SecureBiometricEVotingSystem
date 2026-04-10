/**
 * Shared feature extraction utilities for face and ear recognition.
 *
 * Ported from the web frontend's ear-recognition.service.ts.
 * All browser dependencies (HTMLCanvasElement, ImageData) replaced with
 * a plain PixelBuffer interface that works in React Native.
 */

const RAW_DIM = 512;

/** Platform-agnostic pixel data (replaces browser ImageData). */
export interface PixelBuffer {
  data: Uint8ClampedArray; // RGBA interleaved
  width: number;
  height: number;
}

/** Deterministic PRNG (mulberry32) — identical on every device. */
function mulberry32(seed: number): () => number {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Build a deterministic random projection matrix.
 * Different seed = different feature space (face vs ear).
 */
export function buildProjectionMatrix(
  featureDim: number,
  seed: number,
): Float32Array {
  const rng = mulberry32(seed);
  const matrix = new Float32Array(RAW_DIM * featureDim);
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

/** Project a raw feature vector to the target dimension with L2 normalisation. */
export function project(
  source: Float32Array,
  projectionMatrix: Float32Array,
  featureDim: number,
): Float32Array {
  const out = new Float32Array(featureDim);
  for (let j = 0; j < featureDim; j++) {
    let sum = 0;
    for (let i = 0; i < RAW_DIM; i++) {
      sum += source[i] * projectionMatrix[i * featureDim + j];
    }
    out[j] = sum;
  }
  let norm = 0;
  for (let j = 0; j < featureDim; j++) norm += out[j] * out[j];
  norm = Math.sqrt(norm) || 1;
  for (let j = 0; j < featureDim; j++) out[j] /= norm;
  return out;
}

/**
 * Extract a rich 512-d raw feature vector from pixel data.
 *
 * Features: per-channel statistics, intensity histograms, spatial block
 * means, gradient magnitude/orientation histograms, LBP-like texture.
 * Ported verbatim from the web frontend's ear-recognition.service.ts.
 */
export function extractRawFeatures(pixels: PixelBuffer): Float32Array {
  const { data, width, height } = pixels;
  const features: number[] = [];

  // Per-channel (R, G, B) mean, std, min, max, skewness.
  for (let ch = 0; ch < 3; ch++) {
    let sum = 0, sq = 0, mn = 255, mx = 0;
    const n = width * height;
    for (let i = 0; i < n; i++) {
      const v = data[i * 4 + ch];
      sum += v; sq += v * v;
      if (v < mn) mn = v; if (v > mx) mx = v;
    }
    const mean = sum / n;
    const std = Math.sqrt(sq / n - mean * mean);
    let skew = 0;
    for (let i = 0; i < n; i++) {
      skew += Math.pow((data[i * 4 + ch] - mean) / (std || 1), 3);
    }
    skew /= n;
    features.push(mean / 255, std / 128, mn / 255, mx / 255, skew / 10);
  }

  // Grayscale.
  const gray = new Float32Array(width * height);
  for (let i = 0; i < gray.length; i++) {
    gray[i] = (data[i * 4] * 0.299 + data[i * 4 + 1] * 0.587 + data[i * 4 + 2] * 0.114) / 255;
  }
  let gSum = 0, gSq = 0;
  for (let i = 0; i < gray.length; i++) { gSum += gray[i]; gSq += gray[i] * gray[i]; }
  const gMean = gSum / gray.length;
  const gStd = Math.sqrt(gSq / gray.length - gMean * gMean);
  features.push(gMean, gStd);

  // Intensity histogram (32 bins).
  const histBins = 32;
  const hist = new Float32Array(histBins);
  for (let i = 0; i < gray.length; i++) {
    const bin = Math.min(histBins - 1, Math.floor(gray[i] * histBins));
    hist[bin]++;
  }
  for (let b = 0; b < histBins; b++) hist[b] /= gray.length;
  features.push(...Array.from(hist));

  // Spatial block means (8x8 grid = 64 features).
  const gridSize = 8;
  const bw = Math.floor(width / gridSize);
  const bh = Math.floor(height / gridSize);
  for (let gy = 0; gy < gridSize; gy++) {
    for (let gx = 0; gx < gridSize; gx++) {
      let blockSum = 0, count = 0;
      for (let y = gy * bh; y < (gy + 1) * bh; y++) {
        for (let x = gx * bw; x < (gx + 1) * bw; x++) {
          blockSum += gray[y * width + x];
          count++;
        }
      }
      features.push(blockSum / (count || 1));
    }
  }

  // Gradient magnitude and orientation.
  const gradMag = new Float32Array(width * height);
  const gradOri = new Float32Array(width * height);
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const gx = gray[y * width + (x + 1)] - gray[y * width + (x - 1)];
      const gy2 = gray[(y + 1) * width + x] - gray[(y - 1) * width + x];
      gradMag[y * width + x] = Math.sqrt(gx * gx + gy2 * gy2);
      gradOri[y * width + x] = Math.atan2(gy2, gx);
    }
  }

  // Gradient magnitude stats.
  let mSum = 0, mSq = 0;
  for (let i = 0; i < gradMag.length; i++) { mSum += gradMag[i]; mSq += gradMag[i] * gradMag[i]; }
  const mMean = mSum / gradMag.length;
  const mStd = Math.sqrt(mSq / gradMag.length - mMean * mMean);
  features.push(mMean, mStd);

  // Gradient orientation histogram (16 bins).
  const oriBins = 16;
  const oriHist = new Float32Array(oriBins);
  for (let i = 0; i < gradOri.length; i++) {
    const angle = gradOri[i] + Math.PI;
    const bin = Math.min(oriBins - 1, Math.floor((angle / (2 * Math.PI)) * oriBins));
    oriHist[bin] += gradMag[i];
  }
  let oriTotal = 0;
  for (let b = 0; b < oriBins; b++) oriTotal += oriHist[b];
  for (let b = 0; b < oriBins; b++) oriHist[b] /= (oriTotal || 1);
  features.push(...Array.from(oriHist));

  // Spatial gradient block means (8x8 grid = 64 features).
  for (let gy = 0; gy < gridSize; gy++) {
    for (let gx = 0; gx < gridSize; gx++) {
      let blockSum = 0, count = 0;
      for (let y = gy * bh; y < (gy + 1) * bh; y++) {
        for (let x = gx * bw; x < (gx + 1) * bw; x++) {
          blockSum += gradMag[y * width + x];
          count++;
        }
      }
      features.push(blockSum / (count || 1));
    }
  }

  // LBP-like texture (14x14 grid = 196 features).
  const lbpGrid = 14;
  const lbw = Math.floor(width / lbpGrid);
  const lbh = Math.floor(height / lbpGrid);
  for (let gy = 0; gy < lbpGrid; gy++) {
    for (let gx = 0; gx < lbpGrid; gx++) {
      let cellSum = 0, count = 0;
      for (let y = gy * lbh; y < Math.min((gy + 1) * lbh, height); y++) {
        for (let x = gx * lbw; x < Math.min((gx + 1) * lbw, width); x++) {
          cellSum += gray[y * width + x];
          count++;
        }
      }
      const cellMean = cellSum / (count || 1);
      let bright = 0;
      for (let y = gy * lbh; y < Math.min((gy + 1) * lbh, height); y++) {
        for (let x = gx * lbw; x < Math.min((gx + 1) * lbw, width); x++) {
          if (gray[y * width + x] > cellMean) bright++;
        }
      }
      features.push(bright / (count || 1));
    }
  }

  // Pad/truncate to exactly RAW_DIM.
  const raw = new Float32Array(RAW_DIM);
  raw.set(features.slice(0, RAW_DIM));
  return raw;
}
