import { DecimalPipe, KeyValuePipe, PercentPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';

import { PredictionResponse } from '../../../core/models/prediction.model';

@Component({
  selector: 'app-result-card',
  standalone: true,
  imports: [PercentPipe, KeyValuePipe, DecimalPipe],
  template: `
    <section class="card">
      <h2>Result</h2>
      <div class="verdict" [class.pos]="isPositive()" [class.neg]="!isPositive()">
        <span class="label">{{ isPositive() ? 'Pneumonia pattern detected' : 'No pneumonia pattern detected' }}</span>
        <span class="conf">{{ result().confidence | percent: '1.0-1' }} confidence</span>
      </div>

      @if (result().low_confidence) {
        <p class="low" role="alert">
          ⚠️ The model is not very certain about this image. Treat this result with extra caution.
        </p>
      }

      @if (trueLabel(); as t) {
        <p class="truth" [class.match]="t === result().label" [class.miss]="t !== result().label">
          Dataset label: <strong>{{ t }}</strong> ·
          {{ t === result().label ? '✓ model agrees' : '✗ model disagrees' }}
        </p>
      }

      <h3>Class probabilities</h3>
      @for (p of result().probabilities | keyvalue; track p.key) {
        <div class="row">
          <span class="name">{{ p.key }}</span>
          <div class="track"><div class="fill" [class.pos]="p.key === 'PNEUMONIA'" [style.width.%]="p.value * 100"></div></div>
          <span class="pct">{{ p.value | percent: '1.0-1' }}</span>
        </div>
      }
      <p class="model">Model: {{ result().model_name }}</p>
    </section>
  `,
  styles: [`
    h2 { margin: 0 0 12px; font-size: 18px; } h3 { font-size: 14px; margin: 18px 0 8px; color: var(--muted); }
    .verdict { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap;
               padding: 14px 16px; border-radius: 10px; }
    .verdict.pos { background: var(--bad-bg); color: var(--bad); } .verdict.neg { background: var(--good-bg); color: var(--good); }
    .label { font-weight: 600; font-size: 17px; } .conf { font-size: 14px; }
    .truth { margin: 12px 0 0; font-size: 13px; padding: 8px 12px; border-radius: 8px; background: var(--bg); }
    .truth.match strong, .truth.match { color: var(--good); } .truth.miss strong, .truth.miss { color: var(--bad); }
    .low { background: var(--warn-bg); color: var(--warn-fg); border-radius: 8px; padding: 10px 12px; font-size: 13px; }
    .row { display: grid; grid-template-columns: 100px 1fr 56px; align-items: center; gap: 10px; margin: 6px 0; font-size: 13px; }
    .track { height: 10px; background: var(--border); border-radius: 6px; overflow: hidden; }
    .fill { height: 100%; background: var(--good); } .fill.pos { background: var(--bad); }
    .pct { text-align: right; font-variant-numeric: tabular-nums; } .model { color: var(--muted); font-size: 12px; margin: 14px 0 0; }
  `],
})
export class ResultCardComponent {
  readonly result = input.required<PredictionResponse>();
  /** Ground-truth class when the image comes from the dataset. */
  readonly trueLabel = input<string | null>(null);
  readonly isPositive = computed(() => this.result().label === 'PNEUMONIA');
}
