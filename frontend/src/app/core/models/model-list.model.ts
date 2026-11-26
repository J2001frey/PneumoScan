/** GET /models  (backend/app/routes/compare.py) */
export interface ModelInfo {
  file: string; // checkpoint file name, e.g. "mobilenetv2_weighted_ce.pt"
  name: string; // file name without ".pt"
  architecture: string;
  label: string; // e.g. "MobileNetV2"
  is_default: boolean;
  test_f1: number | null;
  test_recall: number | null;
  test_roc_auc: number | null;
}

export interface ModelListResponse {
  default: string;
  models: ModelInfo[];
}

/** One model's answer in POST /predict/compare */
export interface CompareItem {
  file: string;
  name: string;
  label: string;
  prediction: 'NORMAL' | 'PNEUMONIA' | string | null;
  confidence: number | null; // 0..1
  probabilities: Record<string, number> | null;
  low_confidence: boolean | null;
  ms: number | null;
  error: string | null;
}

export interface CompareResponse {
  results: CompareItem[];
}
