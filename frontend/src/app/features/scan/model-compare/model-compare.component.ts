import { Component, computed, inject, input, signal } from '@angular/core';

import { CompareItem } from '../../../core/models/model-list.model';
import { ModelService } from '../../../core/services/model.service';
import { PredictionService } from '../../../core/services/prediction.service';

interface Stored {
  file: File; // the image these answers belong to
  items: CompareItem[];
}

/** Runs every trained model on the current image and shows their predictions side by side. */
@Component({
  selector: 'app-model-compare',
  standalone: true,
  template: `
    <section class="card">
      <div class="head">
        <h2>Compare models</h2>
        <button class="btn secondary" type="button" [disabled]="!file() || loading()" (click)="run()">
          {{ loading() ? 'Comparing…' : current() ? 'Run again' : 'Compare all models' }}
        </button>
      </div>

      @if (!current() && !loading() && !errorMsg()) {
        <p class="hint">Run every trained model on this same image and see where they agree.</p>
      }
      @if (errorMsg(); as e) { <p class="err" role="alert">{{ e }}</p> }

      @if (current(); as c) {
        <p class="summary" [class.agree]="summary().agree" [class.split]="!summary().agree">{{ summary().text }}</p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="left">Model</th><th>Prediction</th><th>Confidence</th><th>Time</th>
                @if (trueLabel()) { <th>Dataset label</th> }
              </tr>
            </thead>
            <tbody>
              @for (it of c.items; track it.file) {
                <tr [class.active]="it.name === activeModel()">
                  <td class="left">
                    <strong>{{ it.label }}</strong>
                    @if (it.name === activeModel()) { <span class="tag">shown above</span> }
                  </td>
                  @if (it.error) {
                    <td colspan="3" class="bad">{{ it.error }}</td>
                  } @else {
                    <td><span class="pill" [class.pos]="it.prediction === 'PNEUMONIA'" [class.neg]="it.prediction !== 'PNEUMONIA'">{{ it.prediction }}</span></td>
                    <td>{{ pct(it.confidence) }}@if (it.low_confidence) { <span class="warn" title="Below the low-confidence threshold"> ⚠️</span> }</td>
                    <td>{{ it.ms !== null ? it.ms + ' ms' : '–' }}</td>
                  }
                  @if (trueLabel(); as t) {
                    <td [class.good]="!it.error && it.prediction === t" [class.bad]="!it.error && it.prediction !== t">
                      {{ it.error ? '–' : it.prediction === t ? '✓ agrees' : '✗ disagrees' }}
                    </td>
                  }
                </tr>
              }
            </tbody>
          </table>
        </div>
        <p class="hint">Probabilities only; the heatmap and explanation above come from the selected model.</p>
      }
    </section>
  `,
  styles: [`
    .head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
    h2 { margin: 0; font-size: 18px; }
    .btn { padding: 8px 14px; font-size: 14px; }
    .hint { color: var(--muted); font-size: 13px; margin: 12px 0 0; }
    .err { color: var(--bad); font-size: 14px; }
    .summary { margin: 14px 0 10px; padding: 10px 12px; border-radius: 8px; font-size: 14px; font-weight: 600; }
    .summary.agree { background: var(--good-bg); color: var(--good); }
    .summary.split { background: var(--warn-bg); color: var(--warn-fg); }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; font-variant-numeric: tabular-nums; }
    th, td { padding: 9px 10px; text-align: right; white-space: nowrap; border-bottom: 1px solid var(--border); }
    th { font-size: 12px; color: var(--muted); font-weight: 600; }
    th.left, td.left { text-align: left; }
    tbody tr:last-child td { border-bottom: 0; }
    tr.active { background: var(--accent-bg); }
    .tag { margin-left: 8px; font-size: 11px; color: var(--accent); font-weight: 600; }
    .pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .pill.pos { background: var(--bad-bg); color: var(--bad); }
    .pill.neg { background: var(--good-bg); color: var(--good); }
    .good { color: var(--good); } .bad { color: var(--bad); } .warn { font-size: 12px; }
  `],
})
export class ModelCompareComponent {
  private readonly api = inject(ModelService);

  /** The image currently analysed. Answers are discarded automatically when it changes. */
  readonly file = input<File | null>(null);
  /** Ground-truth class when the image comes from the dataset. */
  readonly trueLabel = input<string | null>(null);
  /** Checkpoint name of the model whose full result is shown (e.g. "mobilenetv2_weighted_ce"). */
  readonly activeModel = input<string | null>(null);

  readonly loading = signal(false);
  private readonly stored = signal<Stored | null>(null);
  private readonly failed = signal<{ file: File; message: string } | null>(null);

  /** Only answers for the image that is on screen now. */
  readonly current = computed(() => {
    const s = this.stored();
    return s && s.file === this.file() ? s : null;
  });
  readonly errorMsg = computed(() => {
    const f = this.failed();
    return f && f.file === this.file() ? f.message : null;
  });

  readonly summary = computed(() => {
    const items = (this.current()?.items ?? []).filter((i) => !i.error && i.prediction);
    const pneu = items.filter((i) => i.prediction === 'PNEUMONIA').length;
    const norm = items.length - pneu;
    if (items.length === 0) return { agree: false, text: 'No model could analyse this image.' };
    if (pneu === items.length) return { agree: true, text: `All ${items.length} models agree: PNEUMONIA.` };
    if (norm === items.length) return { agree: true, text: `All ${items.length} models agree: NORMAL.` };
    return { agree: false, text: `The models disagree: ${pneu} predict PNEUMONIA, ${norm} predict NORMAL.` };
  });

  run(): void {
    const f = this.file();
    if (!f || this.loading()) return;
    this.loading.set(true);
    this.failed.set(null);
    this.api.compare(f).subscribe({
      next: (res) => {
        this.stored.set({ file: f, items: res.results });
        this.loading.set(false);
      },
      error: (e) => {
        this.failed.set({ file: f, message: PredictionService.errorMessage(e) });
        this.loading.set(false);
      },
    });
  }

  pct(v: number | null): string {
    return v === null ? '–' : `${(v * 100).toFixed(1)}%`;
  }
}
