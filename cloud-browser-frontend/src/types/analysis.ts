export interface CodeAnalysisRequest {
  code: string
  language: string
  issue_description?: string
}

export interface RepositoryAnalysisRequest {
  github_url: string
  issue_description?: string
  commit_hash?: string
}

export interface FileAnalysisRequest {
  file_path: string
  file_content: string
  language?: string
}

export interface DebugRequest {
  error_message: string
  code_context?: string
  stack_trace?: string
  language?: string
}

export interface AnalysisResult {
  success: boolean
  analysis_id?: string
  repository?: GitHubRepository
  findings?: Finding[]
  suggestions?: Suggestion[]
  file_analysis?: Record<string, FileAnalysis>
  security_issues?: SecurityIssue[]
  performance_issues?: PerformanceIssue[]
  summary?: string
  confidence_score: number
  analyzed_at: string
  error?: string
  details?: any
}

export interface CodeAnalysisResult {
  success: boolean
  analysis_id?: string
  issues?: Issue[]
  suggestions?: Suggestion[]
  improved_code?: string
  explanation?: string
  confidence_score: number
  analyzed_at: string
  error?: string
  details?: any
}

export interface DebugResult {
  success: boolean
  debug_id?: string
  cause_analysis?: string
  solution?: string
  fixed_code?: string
  prevention_tips?: string[]
  related_docs?: DocumentReference[]
  confidence_score: number
  analyzed_at: string
  error?: string
  details?: any
}

export interface FileAnalysisResult {
  success: boolean
  file_path: string
  language: string
  suggestions?: Suggestion[]
  quality_score: number
  issues_found?: Issue[]
  improvements?: Improvement[]
  analyzed_at: string
  error?: string
  details?: any
}

export interface GitHubRepository {
  valid: boolean
  owner: string
  repo: string
  normalized_url: string
  errors?: string[]
}

export interface Finding {
  type: 'bug' | 'vulnerability' | 'code_smell' | 'performance'
  severity: 'low' | 'medium' | 'high' | 'critical'
  file: string
  line?: number
  column?: number
  message: string
  description?: string
  rule?: string
}

export interface Suggestion {
  type: 'improvement' | 'refactor' | 'optimization' | 'best_practice'
  priority: 'low' | 'medium' | 'high'
  file?: string
  line?: number
  title: string
  description: string
  example_code?: string
  benefits?: string[]
}

export interface Issue {
  type: 'syntax' | 'logic' | 'security' | 'performance' | 'style'
  severity: 'error' | 'warning' | 'info'
  line?: number
  column?: number
  message: string
  suggestion?: string
}

export interface SecurityIssue {
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  file: string
  line?: number
  description: string
  recommendation: string
  cwe_id?: string
}

export interface PerformanceIssue {
  type: string
  impact: 'low' | 'medium' | 'high'
  file: string
  line?: number
  description: string
  optimization: string
  estimated_improvement?: string
}

export interface FileAnalysis {
  complexity: number
  maintainability: number
  test_coverage?: number
  issues: Issue[]
  suggestions: Suggestion[]
}

export interface Improvement {
  type: string
  description: string
  impact: 'low' | 'medium' | 'high'
  effort: 'low' | 'medium' | 'high'
  example?: string
}

export interface DocumentReference {
  title: string
  url: string
  description?: string
}

export interface AnalysisStatus {
  success: boolean
  analysis_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  estimated_completion?: string
  current_step?: string
  results_available: boolean
  error?: string
}

export interface AnalysisSession {
  success: boolean
  session_id?: string
  expires_at?: string
  created_at?: string
  error?: string
  details?: any
}

export interface SupportedLanguages {
  languages: string[]
}
