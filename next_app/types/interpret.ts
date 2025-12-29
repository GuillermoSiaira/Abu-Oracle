// next_app/types/interpret.ts

export interface InterpretRequest {
  abuChart: any;
  question: string;
}

export interface InterpretResponse {
  result: string;
  error?: string;
}
