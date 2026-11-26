import { Component } from '@angular/core';

@Component({
  selector: 'app-disclaimer-banner',
  standalone: true,
  template: `
    <div class="banner" role="note">
      <div class="container">
        <strong>Screening aid only.</strong> This tool is not a medical diagnosis. Always have a qualified
        clinician review the original image.
      </div>
    </div>
  `,
  styles: [`
    .banner { background: var(--warn-bg); color: var(--warn-fg); font-size: 13px; padding: 8px 0; border-bottom: 1px solid var(--warn-border); }
  `],
})
export class DisclaimerBannerComponent {}
