// Common API types and interfaces for HTTP requests and responses

export interface ApiResponse<T> {
    data: T
    meta?: PaginationMeta
  }
  
  export interface PaginationMeta {
    page: number
    pageSize: number
    totalPages: number
    totalItems: number
  }
  
  export interface ApiError {
    message: string
    code: string
    details?: Record<string, unknown>
    field?: string
  }
  
  export interface ApiValidationError {
    message: string
    errors: {
      field: string
      message: string
    }[]
  }
  
  export interface RequestConfig {
    method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE"
    headers?: Record<string, string>
    params?: Record<string, string | number | boolean | undefined>
    body?: unknown
    /** When true, do not send Authorization (for public voter-facing reads). */
    omitAuth?: boolean
  }
  
  export interface ApiListResponse<T> {
    items: T[]
    total: number
    page?: number
    pageSize?: number
  }
  
  export class ApiException extends Error {
    constructor(
      message: string,
      public statusCode: number,
      public code?: string,
      public details?: unknown,
    ) {
      super(message)
      this.name = "ApiException"
    }
  }
  
