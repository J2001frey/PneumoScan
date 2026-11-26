PneumoScan - model switcher
===========================
1. Unzip into your project root (overwrite when asked):
     cd ~/Desktop/pneumoscan && unzip -o ~/Downloads/pneumoscan_model_switcher.zip

NEW files:      backend/app/model_registry.py, backend/app/routes/compare.py,
                frontend/src/app/core/models/model-list.model.ts,
                frontend/src/app/core/services/model.service.ts,
                frontend/src/app/features/scan/model-picker/*, .../model-compare/*
REPLACED files: backend/app/predictor.py (additive: new predict_quick),
                backend/app/routes/predict.py (optional model_file form field),
                backend/app/main.py (now includes metrics AND compare routers),
                frontend/src/app/core/services/prediction.service.ts,
                frontend/src/app/features/scan/scan-page/scan-page.component.ts

2. Restart the backend (uvicorn) and `ng serve`.

What you get
- "Model" drop-down above Analyze: switching re-runs the SAME image with that model
  (heatmap + explanation follow the chosen model).
- "Compare models" card: runs every checkpoint in backend/saved_models on the image
  and shows prediction, confidence, time, and agreement with the dataset label.
- GET /models, POST /predict/compare, POST /predict (optional model_file).

If you edited scan-page.component.ts since the earlier patch, don't overwrite it; add:
  imports: ModelPickerComponent, ModelCompareComponent
  template: <app-model-picker [disabled]="loading()" (modelChange)="onModel($event)" /> above the Analyze button
            <app-model-compare [file]="file()" [trueLabel]="trueLabel()" [activeModel]="r.model_name" /> under <app-result-card>
  class: modelFile = signal<string|null>(null); onModel() { ... }; analyze() -> this.api.predict(f, this.modelFile())
