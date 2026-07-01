export interface Project {
  id: number;
  name: string;
  source_lang: string;
  target_lang: string;
  created_at: string;
  updated_at: string;
  total_segments: number;
  translated_segments: number;
}

export interface Document {
  id: number;
  project_id: number;
  filename: string;
  created_at: string;
  segment_count: number;
}

export interface Segment {
  id: number;
  document_id: number;
  segment_index: number;
  source_text: string;
  target_text: string | null;
  status: 'untranslated' | 'draft' | 'translated';
  updated_at: string;
}

export interface TMMatch {
  source_text: string;
  target_text: string;
  score: number;
}

export interface GlossaryTerm {
  source_term: string;
  target_term: string;
  note: string | null;
}

export interface GlossaryEntry {
  id: number;
  source_lang: string;
  target_lang: string;
  source_term: string;
  target_term: string;
  note: string | null;
  created_at: string;
}
