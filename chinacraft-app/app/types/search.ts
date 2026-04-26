export type SearchFilters = {
  topK: number;
  hskLevel?: number;
  strokesMin?: number;
  strokesMax?: number;
};

export type SearchCandidate = {
  char: string;
  score: number;
  pinyin: string[];
  hsk_level?: number;
  strokes?: number;
  translation_ru?: string;
  sample_image?: string;
};

export type SearchResponse = {
  query: string;
  query_type: "text" | "image";
  top_k: number;
  model_version: string;
  index_version: string;
  candidates: SearchCandidate[];
};

