
export interface StreamOptions {
  model?: string;
  onChunk: (chunk: string) => void;
  onComplete: (fullText: string) => void;
  onError: (error: Error) => void;
}

export interface StreamController {
  stop: () => void;
}
