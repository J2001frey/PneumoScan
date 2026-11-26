/** Mirrors backend/app/schemas.py -> PredictionResponse */
export interface PredictionResponse {
  label: 'NORMAL' | 'PNEUMONIA' | string;
  confidence: number; // 0..1
  probabilities: Record<string, number>;
  low_confidence: boolean;
  heatmap_base64: string; // data URI, ready for <img [src]>
  explanation: string;
  disclaimer: string;
  model_name: string;
}

/** Mirrors backend/app/schemas.py -> HealthResponse */
export interface HealthResponse {
  status: string;
  model_file: string;
  model_available: boolean;
  claude_configured: boolean;
}

/** GET /samples  (backend/app/routes/samples.py) */
export interface SampleItem {
  path: string; // e.g. "test/NORMAL/IM-0001.jpeg"
  name: string;
}

export interface SampleListResponse {
  split: string;
  label: string;
  total: number;
  offset: number;
  items: SampleItem[];
}
