import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PredictionResponse } from '../models/prediction.model';

@Injectable({ providedIn: 'root' })
export class PredictionService {
  private readonly http = inject(HttpClient);

  /**
   * POST /predict  (multipart field name must be "file").
   * `modelFile` is optional: a checkpoint name from GET /models. Without it the backend uses its default model.
   */
  predict(file: File, modelFile?: string | null): Observable<PredictionResponse> {
    const form = new FormData();
    form.append('file', file, file.name);
    if (modelFile) form.append('model_file', modelFile);
    return this.http.post<PredictionResponse>(`${environment.apiUrl}/predict`, form);
  }

  /** Turn any HTTP failure into a message a user can act on. */
  static errorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return `Cannot reach the server at ${environment.apiUrl}. Is the backend running?`;
      }
      const detail = err.error?.detail;
      if (typeof detail === 'string') return detail; // FastAPI HTTPException
      if (err.status === 422) return 'The server could not process that upload.';
      return `Request failed (${err.status}).`;
    }
    return 'Something went wrong. Please try again.';
  }
}
