import { Component, input } from '@angular/core';

@Component({
  selector: 'app-ai-report',
  standalone: true,
  template: `
    <section class="card">
      <h2>Plain-language explanation <span class="tag">Claude</span></h2>
      <div class="text">
        @for (p of paragraphs(); track $index) { <p>{{ p }}</p> }
      </div>
      <p class="disc">{{ disclaimer() }}</p>
    </section>
  `,
  styles: [`
    h2 { margin: 0 0 12px; font-size: 18px; display: flex; align-items: center; gap: 8px; }
    .tag { font-size: 11px; font-weight: 600; background: var(--accent-bg); color: var(--accent); padding: 2px 8px; border-radius: 99px; }
    .text p { margin: 0 0 10px; line-height: 1.55; } .disc { margin: 14px 0 0; padding-top: 12px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }
  `],
})
export class AiReportComponent {
  readonly explanation = input.required<string>();
  readonly disclaimer = input.required<string>();

  paragraphs(): string[] {
    return this.explanation().split(/\n{2,}|\n/).map((s) => s.trim()).filter(Boolean);
  }
}
