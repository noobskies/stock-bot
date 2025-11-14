export interface ApiResponse<T = unknown> {
  success?: boolean;
  message?: string;
  error?: string;
  data?: T;
}

export interface ApiError {
  error: string;
  status?: number;
}
