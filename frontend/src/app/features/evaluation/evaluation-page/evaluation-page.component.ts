import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { MetricsResponse, ModelMetrics } from '../../../core/models/metrics.model';
import { MetricsService } from '../../../core/services/metrics.service';
import { environment } from '../../../../environments/environment';

type Kind = 'pct' | 'num3' | 'int' | 'one';
type NumericKey =
  | 'accuracy' | 'recall' | 'specificity' | 'precision' | 'f1' | 'roc_auc'
  | 'fn' | 'fp' | 'ms_per_image' | 'file_size_mb';

interface Column {
  key: NumericKey;
  label: string;
  kind: Kind;
  best: 'max' | 'min';
  hint: string;
}

const COLUMNS: Column[] = [
  { key: 'accuracy', label: 'Accuracy', kind: 'pct', best: 'max', hint: 'Share of all X-rays classified correctly' },
  { key: 'recall', label: 'Recall', kind: 'pct', best: 'max', hint: 'Share of pneumonia cases that were caught' },
  { key: 'specificity', label: 'Specificity', kind: 'pct', best: 'max', hint: 'Share of normal X-rays correctly left alone' },
  { key: 'precision', label: 'Precision', kind: 'pct', best: 'max', hint: 'When it says pneumonia, how often it is right' },
  { key: 'f1', label: 'F1', kind: 'num3', best: 'max', hint: 'Balance of precision and recall' },
  { key: 'roc_auc', label: 'AUC', kind: 'num3', best: 'max', hint: 'Overall ranking quality across all thresholds' },
  { key: 'fn', label: 'Missed pneumonia', kind: 'int', best: 'min', hint: 'Pneumonia X-rays predicted as normal (most serious error)' },
  { key: 'fp', label: 'False alarms', kind: 'int', best: 'min', hint: 'Normal X-rays predicted as pneumonia' },
  { key: 'ms_per_image', label: 'ms / image', kind: 'one', best: 'min', hint: 'Prediction time per image on the machine that ran evaluate.py' },
  { key: 'file_size_mb', label: 'Size (MB)', kind: 'one', best: 'min', hint: 'Size of the saved model file' },
];

@Component({
  selector: 'app-evaluation-page',
  standalone: true,
  template: `
    <h1>Model evaluation</h1>
    <p class="sub">
      All models were evaluated on the same held-out test set
      @if (data(); as d) { ({{ d.test_size }} images). }
    </p>

    @if (status() === 'loading') {
      <div class="card note">Loading evaluation results…</div>
    }

    @if (status() === 'error') {
      <div class="card error" role="alert">{{ error() }}</div>
    }

    @if (data(); as d) {
      @if (winner(); as w) {
        <section class="card winner">
          <span class="badge">Best overall</span>
          <h2>{{ w.model }}</h2>
          <p>
            Highest F1 ({{ w.f1.toFixed(3) }}), AUC {{ w.roc_auc.toFixed(3) }}, and
            {{ w.fn }} missed pneumonia case{{ w.fn === 1 ? '' : 's' }} out of {{ w.fn + w.tp }}.
          </p>
        </section>
      }

      <section class="card">
        <h2>Test-set results</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="left">Model</th>
                @for (c of columns; track c.key) {
                  <th [title]="c.hint">{{ c.label }}</th>
                }
              </tr>
            </thead>
            <tbody>
              @for (m of d.models; track m.name) {
                <tr>
                  <td class="left">
                    <strong>{{ m.model }}</strong>
                    <span class="loss">{{ m.loss }}</span>
                  </td>
                  @for (c of columns; track c.key) {
                    <td [class.best]="isBest(c, m)">{{ cell(c, m) }}</td>
                  }
                </tr>
              }
            </tbody>
          </table>
        </div>
        <p class="legend"><span class="swatch"></span> best value in each column. Hover a column title for its meaning.</p>

        <details>
          <summary>How to read this</summary>
          <ul>
            <li><strong>Missed pneumonia</strong> is the most serious error for a screening tool, so lower is better.</li>
            <li><strong>False alarms</strong> are normal X-rays flagged as pneumonia. They cost follow-up time, not safety.</li>
            <li><strong>AUC</strong> compares the models without depending on a single threshold.</li>
            <li>Speed depends on the computer used to run the evaluation.</li>
          </ul>
        </details>
      </section>

      @if (has('class_distribution.png')) {
        <figure class="card wide">
          <h2>Dataset class distribution</h2>
          <img [src]="url('class_distribution.png')" alt="Number of NORMAL and PNEUMONIA images in the train, validation and test splits" loading="lazy" />
          <figcaption>
            Pneumonia images outnumber normal ones, so training used class-weighted cross-entropy.
          </figcaption>
        </figure>
      }

      @if (has('roc_comparison.png') || has('model_comparison.png')) {
        <section class="grid two">
          @if (has('roc_comparison.png')) {
            <figure class="card">
              <img [src]="url('roc_comparison.png')" alt="ROC curves of all models on the test set" loading="lazy" />
              <figcaption>ROC curves (test set)</figcaption>
            </figure>
          }
          @if (has('model_comparison.png')) {
            <figure class="card">
              <img [src]="url('model_comparison.png')" alt="Bar chart comparing the models on each metric" loading="lazy" />
              <figcaption>Metrics side by side</figcaption>
            </figure>
          }
        </section>
      }

      @for (m of d.models; track m.name) {
        @if (has('confusion_' + m.name + '.png') || has('curves_' + m.name + '.png')) {
          <section class="card">
            <h2>{{ m.model }}</h2>
            <div class="pair">
              @if (has('confusion_' + m.name + '.png')) {
                <figure>
                  <img [src]="url('confusion_' + m.name + '.png')" [alt]="'Confusion matrix of ' + m.model" loading="lazy" />
                  <figcaption>Confusion matrix (test set)</figcaption>
                </figure>
              }
              @if (has('curves_' + m.name + '.png')) {
                <figure>
                  <img [src]="url('curves_' + m.name + '.png')" [alt]="'Training curves of ' + m.model" loading="lazy" />
                  <figcaption>Training curves (loss and validation metrics)</figcaption>
                </figure>
              }
            </div>
          </section>
        }
      }

      <p class="foot">
        Research and teaching tool, not a medical device. Validation scores during training are optimistic;
        the test-set numbers above are the ones to report.
      </p>
    }
  `,
  styles: [
    `
      :host { display: block; }
      h1 { margin: 0 0 4px; font-size: 1.6rem; }
      h2 { margin: 0 0 12px; font-size: 1.1rem; }
      .sub { margin: 0 0 20px; color: var(--muted); }
      .card { margin-bottom: 20px; }
      .note { color: var(--muted); }
      .error { background: var(--bad-bg); color: var(--bad); border-color: var(--bad); }

      .winner { background: var(--good-bg); border-color: var(--good); }
      .winner h2 { margin: 6px 0 4px; font-size: 1.3rem; }
      .winner p { margin: 0; }
      .badge {
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        background: var(--good); color: var(--bg); font-size: .75rem; font-weight: 700;
      }

      .table-wrap { overflow-x: auto; }
      table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
      th, td { padding: 10px 12px; text-align: right; white-space: nowrap; border-bottom: 1px solid var(--border); }
      th { font-size: .8rem; color: var(--muted); font-weight: 600; cursor: help; }
      th.left, td.left { text-align: left; }
      tbody tr:last-child td { border-bottom: 0; }
      td.best { background: var(--good-bg); color: var(--good); font-weight: 700; }
      .loss { display: block; font-size: .75rem; color: var(--muted); }

      .legend { margin: 12px 0 0; font-size: .8rem; color: var(--muted); }
      .swatch {
        display: inline-block; width: 12px; height: 12px; border-radius: 3px;
        background: var(--good-bg); border: 1px solid var(--good); vertical-align: -1px;
      }
      details { margin-top: 12px; color: var(--muted); font-size: .9rem; }
      summary { cursor: pointer; color: var(--accent); font-weight: 600; }

      .grid { display: grid; gap: 20px; }
      .grid.two { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
      .grid > .card { margin-bottom: 0; display: flex; flex-direction: column; justify-content: center; }
      section.grid { margin-bottom: 20px; }
      /* confusion matrix (squarer) gets less width than the wide training curves, both centred vertically */
      .pair { display: grid; grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.5fr); gap: 20px; align-items: center; }
      @media (max-width: 760px) { .pair { grid-template-columns: 1fr; } }
      figure { margin: 0; }
      figure.wide img { max-width: 880px; margin: 0 auto; }
      img { display: block; width: 100%; height: auto; background: #fff; border-radius: 8px; }
      figcaption { margin-top: 8px; font-size: .85rem; color: var(--muted); text-align: center; }
      .foot { color: var(--muted); font-size: .8rem; margin: 8px 0 32px; }
    `,
  ],
})
export class EvaluationPageComponent implements OnInit {
  private readonly api = inject(MetricsService);

  readonly columns = COLUMNS;
  readonly status = signal<'loading' | 'ready' | 'error'>('loading');
  readonly error = signal('');
  readonly data = signal<MetricsResponse | null>(null);

  readonly winner = computed(() => this.data()?.models[0] ?? null); // backend sorts by F1, best first

  private readonly bestValues = computed(() => {
    const out = new Map<NumericKey, number>();
    const models = this.data()?.models ?? [];
    for (const c of COLUMNS) {
      const vals = models.map((m) => m[c.key]).filter((v): v is number => typeof v === 'number');
      if (vals.length) out.set(c.key, c.best === 'max' ? Math.max(...vals) : Math.min(...vals));
    }
    return out;
  });

  private readonly plotSet = computed(() => new Set(this.data()?.plots ?? []));

  ngOnInit(): void {
    this.api.getMetrics().subscribe({
      next: (res) => {
        this.data.set(res);
        this.status.set('ready');
      },
      error: (err: HttpErrorResponse) => {
        this.status.set('error');
        if (err.status === 0) {
          this.error.set(`Cannot reach the server at ${environment.apiUrl}. Is the backend running?`);
        } else {
          this.error.set(err.error?.detail ?? `The server returned an error (${err.status}).`);
        }
      },
    });
  }

  has(file: string): boolean {
    return this.plotSet().has(file);
  }

  url(file: string): string {
    return this.api.plotUrl(file);
  }

  isBest(c: Column, m: ModelMetrics): boolean {
    const v = m[c.key];
    return typeof v === 'number' && v === this.bestValues().get(c.key) && this.data()!.models.length > 1;
  }

  cell(c: Column, m: ModelMetrics): string {
    const v = m[c.key];
    if (typeof v !== 'number') return '–';
    switch (c.kind) {
      case 'pct': return `${(v * 100).toFixed(1)}%`;
      case 'num3': return v.toFixed(3);
      case 'one': return v.toFixed(1);
      default: return String(v);
    }
  }
}