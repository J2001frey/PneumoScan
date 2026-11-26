import { Component, input, signal } from '@angular/core';

@Component({
  selector: 'app-gradcam-viewer',
  standalone: true,
  template: `
    <section class="card">
      <h2>Model attention (Grad-CAM)</h2>
      <p class="sub">Warmer areas show regions that influenced the model most. This is not a lesion outline.</p>

      <div class="stage">
        <img class="base" [src]="originalUrl()" alt="Original chest X-ray" />
        <img class="heat" [src]="heatmapUrl()" [style.opacity]="opacity() / 100" alt="Grad-CAM heatmap overlay" />
      </div>

      <label class="slider">
        <span>Original</span>
        <input type="range" min="0" max="100" [value]="opacity()" (input)="onSlide($event)"
               aria-label="Heatmap opacity" />
        <span>Heatmap</span>
      </label>
    </section>
  `,
  styles: [`
    h2 { margin: 0 0 4px; font-size: 18px; } .sub { margin: 0 0 12px; color: var(--muted); font-size: 13px; }
    .stage { position: relative; background: #000; border-radius: 10px; overflow: hidden; line-height: 0; }
    .stage img { width: 100%; display: block; }
    .heat { position: absolute; inset: 0; height: 100%; object-fit: fill; transition: opacity .1s; }
    .slider { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: center; margin-top: 12px; font-size: 13px; color: var(--muted); }
  `],
})
export class GradcamViewerComponent {
  readonly originalUrl = input.required<string>();
  /** data URI from the backend (already an overlay of heatmap on the X-ray) */
  readonly heatmapUrl = input.required<string>();
  readonly opacity = signal(100);

  onSlide(e: Event): void {
    this.opacity.set(Number((e.target as HTMLInputElement).value));
  }
}
