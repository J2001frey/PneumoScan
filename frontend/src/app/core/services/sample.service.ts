import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { SampleListResponse } from '../models/prediction.model';

@Injectable({ providedIn: 'root' })
export class SampleService {
  private readonly http = inject(HttpClient);

  list(split: string, label: string, offset = 0, limit = 24): Observable<SampleListResponse> {
    return this.http.get<SampleListResponse>(`${environment.apiUrl}/samples`, {
      params: { split, label, offset, limit },
    });
  }

  /** URL usable directly in <img src>. */
  imageUrl(path: string, thumb = false): string {
    const q = `path=${encodeURIComponent(path)}${thumb ? '&thumb=true' : ''}`;
    return `${environment.apiUrl}/samples/image?${q}`;
  }

  /** Download the full image and wrap it as a File so it can go through /predict. */
  fetchAsFile(path: string): Observable<File> {
    const name = path.split('/').pop() ?? 'sample.jpeg';
    return this.http
      .get(this.imageUrl(path), { responseType: 'blob' })
      .pipe(map((blob) => new File([blob], name, { type: blob.type || guessType(name) })));
  }
}

function guessType(name: string): string {
  return name.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
}
