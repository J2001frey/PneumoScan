import { Component, inject, signal } from '@angular/core';

import { PredictionResponse } from '../../../core/models/prediction.model';
import { PredictionService } from '../../../core/services/prediction.service';
import { AiReportComponent } from '../ai-report/ai-report.component';
import { GradcamViewerComponent } from '../gradcam-viewer/gradcam-viewer.component';
import { ImageUploadComponent } from '../image-upload/image-upload.component';
import { ModelCompareComponent } from '../model-compare/model-compare.component';
import { ModelPickerComponent } from '../model-picker/model-picker.component';
import { ResultCardComponent } from '../result-card/result-card.component';
import { PickedSample, SampleBrowserComponent } from '../sample-browser/sample-browser.component';

type Mode = 'dataset' | 'upload';

@Component({
  selector: 'app-scan-page',
  standalone: true,
  imports: [
    ImageUploadComponent, SampleBrowserComponent, ResultCardComponent, GradcamViewerComponent, AiReportComponent,
    ModelPickerComponent, ModelCompareComponent,
  ],
  template: `
    <div class="grid">
      <div class="col">
        <section class="card">
          <h2>1. Choose an X-ray</h2>
          <div class="modes" role="tablist">
            <button type="button" role="tab" [class.on]="mode() === 'dataset'" (click)="setMode('dataset')">Dataset images</button>
            <button type="button" role="tab" [class.on]="mode() === 'upload'" (click)="setMode('upload')">Upload your own</button>
          </div>

          @if (mode() === 'dataset') {
            <app-sample-browser (picked)="onSample($event)" />
            @if (originalUrl(); as o) {
              <div class="selected">
                <img [src]="o" alt="Selected X-ray" />
                <span>{{ sampleName() }}</span>
              </div>
            }
          } @else {
            <app-image-upload (fileChange)="onFile($event)" />
          }

          <app-model-picker [disabled]="loading()" (modelChange)="onModel($event)" />

          <button class="btn" type="button" [disabled]="!file() || loading()" (click)="analyze()">
            {{ loading() ? 'Analyzing…' : 'Analyze image' }}
          </button>
          @if (loading()) { <p class="sub">Running the model and generating the explanation. This can take several seconds.</p> }
          @if (error(); as e) { <p class="err" role="alert">{{ e }}</p> }
        </section>
      </div>

      <div class="col">
        @if (result(); as r) {
          <app-result-card [result]="r" [trueLabel]="trueLabel()" />
          <app-model-compare [file]="file()" [trueLabel]="trueLabel()" [activeModel]="r.model_name" />
          @if (originalUrl(); as o) { <app-gradcam-viewer [originalUrl]="o" [heatmapUrl]="r.heatmap_base64" /> }
          <app-ai-report [explanation]="r.explanation" [disclaimer]="r.disclaimer" />
        } @else {
          <section class="card empty">
            <h2>2. Results</h2>
            <p>Click an image from <code>backend/data/chest_xray</code> (or upload your own) to see the prediction,
              the Grad-CAM heatmap and a plain-language explanation.</p>
          </section>
        }
      </div>
    </div>
  `,
  styles: [`
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
    .col { display: flex; flex-direction: column; gap: 20px; }
    @media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
    h2 { margin: 0 0 12px; font-size: 18px; } .sub { color: var(--muted); font-size: 13px; }
    .modes { display: flex; gap: 6px; margin-bottom: 14px; }
    .modes button { flex: 1; font: inherit; font-size: 14px; padding: 8px; border-radius: 10px; border: 1px solid var(--border);
                    background: var(--surface); color: var(--text); cursor: pointer; }
    .modes button.on { background: var(--accent-bg); color: var(--accent); border-color: var(--accent); font-weight: 600; }
    .selected { display: flex; align-items: center; gap: 12px; margin-top: 14px; font-size: 13px; color: var(--muted); }
    .selected img { width: 72px; height: 72px; object-fit: cover; border-radius: 8px; background: #000; }
    .btn { margin-top: 14px; width: 100%; } .err { color: var(--bad); font-size: 14px; } .empty p { color: var(--muted); line-height: 1.55; }
  `],
})
export class ScanPageComponent {
  private readonly api = inject(PredictionService);

  readonly mode = signal<Mode>('dataset');
  readonly file = signal<File | null>(null);
  readonly originalUrl = signal<string | null>(null);
  readonly trueLabel = signal<string | null>(null);
  readonly sampleName = signal('');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<PredictionResponse | null>(null);
  /** Checkpoint chosen in the model picker (null = let the backend use its default). */
  readonly modelFile = signal<string | null>(null);

  setMode(m: Mode): void {
    if (m === this.mode()) return;
    this.mode.set(m);
    this.reset(null);
  }

  /** Image chosen from backend/data/chest_xray: analyze right away. */
  onSample(s: PickedSample): void {
    this.reset(s.file);
    this.trueLabel.set(s.trueLabel);
    this.sampleName.set(s.path);
    this.analyze();
  }

  /** Image chosen from the upload box (no ground truth known). */
  onFile(f: File | null): void {
    this.reset(f);
  }

  /** Another model was chosen: analyze the same image again with it. */
  onModel(modelFile: string): void {
    const changed = this.modelFile() !== modelFile;
    this.modelFile.set(modelFile);
    if (changed && this.file() && this.result()) this.analyze();
  }

  analyze(): void {
    const f = this.file();
    if (!f || this.loading()) return;
    this.loading.set(true);
    this.error.set(null);
    this.result.set(null);
    this.api.predict(f, this.modelFile()).subscribe({
      next: (r) => { this.result.set(r); this.loading.set(false); },
      error: (e) => { this.error.set(PredictionService.errorMessage(e)); this.loading.set(false); },
    });
  }

  private reset(f: File | null): void {
    const old = this.originalUrl();
    if (old) URL.revokeObjectURL(old);
    this.file.set(f);
    this.originalUrl.set(f ? URL.createObjectURL(f) : null);
    this.trueLabel.set(null);
    this.sampleName.set('');
    this.result.set(null);
    this.error.set(null);
  }
}
