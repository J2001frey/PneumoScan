import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-nav-tabs',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav class="tabs" aria-label="Pages">
      <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Analyse X-ray</a>
      <a routerLink="/evaluation" routerLinkActive="active">Model evaluation</a>
    </nav>
  `,
  styles: [
    `
      .tabs {
        display: flex;
        gap: 6px;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border);
      }
      a {
        padding: 10px 16px;
        color: var(--muted);
        text-decoration: none;
        font-weight: 600;
        border-bottom: 3px solid transparent;
        margin-bottom: -1px;
      }
      a:hover {
        color: var(--text);
      }
      a.active {
        color: var(--accent);
        border-bottom-color: var(--accent);
      }
    `,
  ],
})
export class NavTabsComponent {}
