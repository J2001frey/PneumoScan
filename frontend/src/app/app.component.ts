import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { DisclaimerBannerComponent } from './shared/disclaimer-banner/disclaimer-banner.component';
import { HeaderComponent } from './shared/header/header.component';
import { NavTabsComponent } from './shared/nav-tabs/nav-tabs.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, DisclaimerBannerComponent, NavTabsComponent],
  template: `
    <app-header />
    <app-disclaimer-banner />
    <main class="container">
      <app-nav-tabs />
      <router-outlet />
    </main>
  `,
})
export class AppComponent {}
