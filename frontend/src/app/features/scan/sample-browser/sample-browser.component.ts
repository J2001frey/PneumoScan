import { Component, OnInit, inject, output, signal } from '@angular/core';

import { SampleItem } from '../../../core/models/prediction.model';
import { PredictionService } from '../../../core/services/prediction.service';
import { SampleService } from '../../../core/services/sample.service';

export interface PickedSample {
  file: File;
  path: string;
  /** Ground-truth class taken from the dataset folder name. */
  trueLabel: string;
}

@Component({
  selector: 'app-sample-browser',
  standalone: true,
  template: `
    <div class="controls">
      <label>Split
        <select [value]="split()" (change)="setSplit($event)">
          @for (s of splits; track s) { <option [value]="s">{{ s }}</option> }
        </select>
      </label>
      <div class="tabs" role="tablist">
        @for (l of labels; track l) {
          <button type="button" role="tab" [class.on]="label() === l" (click)="setLabel(l)">{{ l }}</button>
        }
      </div>
    </div>

    <p class="count">
      {{ total() }} image{{ total() === 1 ? '' : 's' }} in <code>data/chest_xray/{{ split() }}/{{ label() }}</code>
    </p>

    @if (error(); as e) { <p class="err" role="alert">{{ e }}</p> }

    <div class="grid">
      @for (it of items(); track it.path) {
        <button type="button" class="thumb" [class.sel]="selected() === it.path" [disabled]="busy()"
                (click)="pick(it)" [title]="it.name">
          <img [src]="svc.imageUrl(it.path, true)" [alt]="it.name" loading="lazy" />
        </button>
      }
    </div>

    @if (!loading() && !error() && total() === 0) {
      <p class="empty">No images found here. Check that the dataset is inside backend/data/chest_xray.</p>
    }
    @if (items().length < total()) {
      <button type="button" class="btn secondary more" [disabled]="loading()" (click)="load(false)">
        {{ loading() ? 'Loading…' : 'Load more' }}
      </button>
    }
  `,
  styles: [`
    .controls { display: flex; gap: 12px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    label { font-size: 13px; color: var(--muted); display: flex; gap: 8px; align-items: center; }
    select { font: inherit; padding: 6px 8px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); color: var(--text); }
    .tabs { display: flex; gap: 6px; }
    .tabs button { font: inherit; font-size: 13px; padding: 6px 12px; border-radius: 99px; border: 1px solid var(--border);
                   background: var(--surface); color: var(--text); cursor: pointer; }
    .tabs button.on { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
    .count { font-size: 12px; color: var(--muted); margin: 10px 0; } code { font-size: 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); gap: 8px; max-height: 340px; overflow-y: auto; padding: 2px; }
    .thumb { padding: 0; border: 2px solid transparent; border-radius: 8px; overflow: hidden; background: #000; cursor: pointer; aspect-ratio: 1; }
    .thumb:hover { border-color: var(--accent); } .thumb.sel { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-bg); }
    .thumb:disabled { opacity: .6; cursor: progress; }
    .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .more { margin-top: 10px; width: 100%; } .err { color: var(--bad); font-size: 13px; } .empty { color: var(--muted); font-size: 13px; }
  `],
})
export class SampleBrowserComponent implements OnInit {
  protected readonly svc = inject(SampleService);

  readonly picked = output<PickedSample>();

  readonly splits = ['test', 'train'];
  readonly labels = ['NORMAL', 'PNEUMONIA'];
  readonly split = signal('test');
  readonly label = signal('NORMAL');

  readonly items = signal<SampleItem[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly selected = signal<string | null>(null);

  ngOnInit(): void { this.load(true); }

  setSplit(e: Event): void { this.split.set((e.target as HTMLSelectElement).value); this.load(true); }
  setLabel(l: string): void { this.label.set(l); this.load(true); }

  load(reset: boolean): void {
    if (reset) { this.items.set([]); this.total.set(0); }
    this.loading.set(true);
    this.error.set(null);
    this.svc.list(this.split(), this.label(), this.items().length).subscribe({
      next: (r) => {
        this.items.update((cur) => [...cur, ...r.items]);
        this.total.set(r.total);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(
          e?.status === 404
            ? 'The backend has no /samples endpoint yet. Add routes/samples.py and restart the server.'
            : PredictionService.errorMessage(e),
        );
        this.loading.set(false);
      },
    });
  }

  pick(it: SampleItem): void {
    this.selected.set(it.path);
    this.busy.set(true);
    this.svc.fetchAsFile(it.path).subscribe({
      next: (file) => {
        this.busy.set(false);
        this.picked.emit({ file, path: it.path, trueLabel: it.path.split('/')[1] });
      },
      error: (e) => { this.busy.set(false); this.error.set(PredictionService.errorMessage(e)); },
    });
  }
}