import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/scan/scan-page/scan-page.component').then((m) => m.ScanPageComponent),
  },
  {
    path: 'evaluation',
    loadComponent: () =>
      import('./features/evaluation/evaluation-page/evaluation-page.component').then(
        (m) => m.EvaluationPageComponent,
      ),
  },
  { path: '**', redirectTo: '' },
];
