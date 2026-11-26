import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { MetricsResponse } from '../models/metrics.model';

@Injectable({ providedIn: 'root' })
export class MetricsService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getMetrics(): Observable<MetricsResponse> {
    return this.http.get<MetricsResponse>(`${this.base}/metrics`);
  }

  plotUrl(filename: string): string {
    return `${this.base}/metrics/plot/${encodeURIComponent(filename)}`;
  }
}
