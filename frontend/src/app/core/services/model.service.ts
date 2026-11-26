import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CompareResponse, ModelListResponse } from '../models/model-list.model';

@Injectable({ providedIn: 'root' })
export class ModelService {
  private readonly http = inject(HttpClient);

  /** GET /models */
  list(): Observable<ModelListResponse> {
    return this.http.get<ModelListResponse>(`${environment.apiUrl}/models`);
  }

  /** POST /predict/compare  (multipart field name must be "file") */
  compare(file: File): Observable<CompareResponse> {
    const form = new FormData();
    form.append('file', file, file.name);
    return this.http.post<CompareResponse>(`${environment.apiUrl}/predict/compare`, form);
  }
}
