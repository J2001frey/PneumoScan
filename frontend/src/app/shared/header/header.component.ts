import { Component, OnInit, inject, signal } from '@angular/core';

import { HealthResponse } from '../../core/models/prediction.model';
import { HealthService } from '../../core/services/health.service';

@Component({
  selector: 'app-header',
  standalone: true,
  template: `
    <header class="bar">
      <div class="container bar-inner">
        <div class="brand">
          <span class="logo" aria-hidden="true">🫁</span>
          <div>
            <h1>PneumoScan</h1>
            <p>AI-assisted chest X-ray screening</p>
          </div>
        </div>
        <div class="status" [class.ok]="state() === 'ok'" [class.warn]="state() === 'warn'"
             [class.down]="state() === 'down'" [title]="detail()">
          <span class="dot"></span>{{ label() }}
        </div>
      </div>
    </header>
  `,
  styles: [`
    .bar { background: var(--surface); border-bottom: 1px solid var(--border); }
    .bar-inner { display: flex; align-items: center; justify-content: space-between; padding-block: 14px; gap: 12px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo { font-size: 28px; }
    h1 { margin: 0; font-size: 20px; }
    p { margin: 0; color: var(--muted); font-size: 13px; }
    .status { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--muted); }
    .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--muted); }
    .ok .dot { background: var(--good); } .warn .dot { background: var(--warn); } .down .dot { background: var(--bad); }
  `],
})
export class HeaderComponent implements OnInit {
  private readonly health = inject(HealthService);
  readonly state = signal<'checking' | 'ok' | 'warn' | 'down'>('checking');
  readonly label = signal('Checking server…');
  readonly detail = signal('');

  ngOnInit(): void {
    this.health.check().subscribe({
      next: (h: HealthResponse) => {
        if (!h.model_available) {
          this.state.set('warn');
          this.label.set('Model file missing');
          this.detail.set(`Backend expects saved_models/${h.model_file}. Set MODEL_FILE in backend/.env.`);
        } else if (!h.claude_configured) {
          this.state.set('warn');
          this.label.set('Online · basic explanations');
          this.detail.set('ANTHROPIC_API_KEY is not set, so Claude reports use a fallback template.');
        } else {
          this.state.set('ok');
          this.label.set('Online');
          this.detail.set(`Model: ${h.model_file}`);
        }
      },
      error: () => {
        this.state.set('down');
        this.label.set('Server offline');
        this.detail.set('Start the backend: uvicorn app.main:app --reload');
      },
    });
  }
}
