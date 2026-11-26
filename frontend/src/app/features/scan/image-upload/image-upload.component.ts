import { Component, OnDestroy, output, signal } from '@angular/core';

const ALLOWED = ['image/jpeg', 'image/jpg', 'image/png'];
const MAX_MB = 10; // keep in sync with MAX_UPLOAD_MB in backend/app/config.py

@Component({
  selector: 'app-image-upload',
  standalone: true,
  template: `
    <div class="drop" [class.over]="dragging()" [class.has]="previewUrl()"
         (dragover)="onDragOver($event)" (dragleave)="dragging.set(false)" (drop)="onDrop($event)">
      @if (previewUrl(); as url) {
        <img [src]="url" alt="Selected chest X-ray preview" />
        <div class="meta">
          <span>{{ fileName() }}</span>
          <button type="button" class="link" (click)="clear()">Remove</button>
        </div>
      } @else {
        <div class="hint">
          <div class="icon" aria-hidden="true">⬆️</div>
          <p><strong>Drag &amp; drop a chest X-ray</strong></p>
          <p class="sub">JPEG or PNG, up to {{ maxMb }} MB</p>
          <label class="btn secondary">
            Choose file
            <input type="file" accept="image/jpeg,image/png" (change)="onPick($event)" hidden />
          </label>
        </div>
      }
    </div>
    @if (error(); as e) { <p class="err" role="alert">{{ e }}</p> }
  `,
  styles: [`
    .drop { border: 2px dashed var(--border); border-radius: 14px; background: var(--surface); min-height: 280px;
            display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 16px; transition: .15s; }
    .drop.over { border-color: var(--accent); background: var(--accent-bg); }
    .drop.has { border-style: solid; }
    img { max-width: 100%; max-height: 360px; border-radius: 8px; background: #000; }
    .meta { display: flex; gap: 12px; align-items: center; margin-top: 10px; font-size: 13px; color: var(--muted); }
    .hint { text-align: center; } .icon { font-size: 34px; } .sub { color: var(--muted); font-size: 13px; }
    .link { background: none; border: 0; color: var(--accent); cursor: pointer; text-decoration: underline; font: inherit; }
    .err { color: var(--bad); font-size: 13px; margin: 8px 0 0; }
  `],
})
export class ImageUploadComponent implements OnDestroy {
  /** Emits the chosen file, or null when cleared. */
  readonly fileChange = output<File | null>();

  readonly maxMb = MAX_MB;
  readonly dragging = signal(false);
  readonly previewUrl = signal<string | null>(null);
  readonly fileName = signal('');
  readonly error = signal<string | null>(null);

  onDragOver(e: DragEvent): void { e.preventDefault(); this.dragging.set(true); }

  onDrop(e: DragEvent): void {
    e.preventDefault();
    this.dragging.set(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) this.accept(f);
  }

  onPick(e: Event): void {
    const input = e.target as HTMLInputElement;
    const f = input.files?.[0];
    if (f) this.accept(f);
    input.value = ''; // allow re-selecting the same file
  }

  clear(): void {
    this.revoke();
    this.previewUrl.set(null);
    this.fileName.set('');
    this.error.set(null);
    this.fileChange.emit(null);
  }

  ngOnDestroy(): void { this.revoke(); }

  private accept(file: File): void {
    if (!ALLOWED.includes(file.type)) {
      this.error.set('Please choose a JPEG or PNG image.');
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      this.error.set(`That image is larger than ${MAX_MB} MB.`);
      return;
    }
    this.error.set(null);
    this.revoke();
    this.previewUrl.set(URL.createObjectURL(file));
    this.fileName.set(file.name);
    this.fileChange.emit(file);
  }

  private revoke(): void {
    const url = this.previewUrl();
    if (url) URL.revokeObjectURL(url);
  }
}
