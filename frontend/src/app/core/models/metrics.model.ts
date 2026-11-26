export interface ModelMetrics {
  name: string;
  model: string;
  loss: string;
  accuracy: number;
  precision: number;
  recall: number;
  specificity: number;
  f1: number;
  roc_auc: number;
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  ms_per_image: number | null;
  parameters_millions: number | null;
  file_size_mb: number | null;
}

export interface MetricsResponse {
  models: ModelMetrics[];
  test_size: number;
  plots: string[];
}
