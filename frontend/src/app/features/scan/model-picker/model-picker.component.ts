import { Component, OnInit, inject, input, output, signal } from '@angular/core';

import { ModelInfo } from '../../../core/models/model-list.model';
import { ModelService } from '../../../core/services/model.service';

/** Drop-down that lets the user choose which trained model analyses the image. */
@Component({
  selector: 'app-model-picker',
  standalone: true,
  template: `
    <div class="picker">
      <label for="model-select">Model</label>
      <select id="model-select" [disabled]="disabled() || models().length < 2" (change)="onChange($event)">
        @for (m of models(); track m.file) {
          <option [value]="m.file" [selected]="m.file === selected()">
            {{ m.label }}{{ m.is_default ? ' (default)' : '' }}{{ m.test_f1 !== null ? ' · test F1 ' + m.test_f1.toFixed(3) : '' }}
          </option>
        }
      </select>
    </div>
    @if (models().length > 1) {
      <p class="hint">Changing the model re-runs the analysis on the same image.</p>
    }
  `,
  styles: [`
    .picker { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
    label { font-size: 13px; color: var(--muted); }
    select { flex: 1; min-width: 0; font: inherit; font-size: 14px; padding: 8px 10px; border-radius: 10px;
             border: 1px solid var(--border); background: var(--surface); color: var(--text); }
    select:disabled { opacity: .6; }
    .hint { margin: 6px 0 0; font-size: 12px; color: var(--muted); }
  `],
})
export class ModelPickerComponent implements OnInit {
  private readonly api = inject(ModelService);

  readonly disabled = input(false);
  /** Emits the chosen checkpoint file name (also once at start, with the default model). */
  readonly modelChange = output<string>();

  readonly models = signal<ModelInfo[]>([]);
  readonly selected = signal<string>('');

  ngOnInit(): void {
    this.api.list().subscribe({
      next: (res) => {
        this.models.set(res.models);
        const start = res.models.find((m) => m.file === res.default) ?? res.models[0];
        if (start) {
          this.selected.set(start.file);
          this.modelChange.emit(start.file);
        }
      },
      // Older backend or server offline: the page keeps working with the backend's default model.
      error: () => this.models.set([]),
    });
  }

  onChange(ev: Event): void {
    const file = (ev.target as HTMLSelectElement).value;
    if (file === this.selected()) return;
    this.selected.set(file);
    this.modelChange.emit(file);
  }
}
