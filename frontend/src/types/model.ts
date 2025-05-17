export interface ModelPerformance {
  rank?: number;
  successRate?: number;
  taskSuccessRate?: number;
  totalRequests?: number;
  avgLatency?: number;
}

export interface ModelOption {
  id: string;
  label: string;
  description: string;
  requiresSubscription: boolean;
  capabilities?: string[];
  performance?: ModelPerformance;
}

export interface ModelSuggestionResponse {
  suggested_model: string;
  ranked_models: Array<{
    model_id: string;
    performance: ModelPerformance;
  }>;
  task_type?: string;
  confidence?: number;
  use_user_selection?: boolean;
}

export const DEFAULT_MODEL = 'openrouter/mistralai/mistral-7b-instruct:free';

export const MODEL_OPTIONS: ModelOption[] = [
  { 
    id: 'openrouter/mistralai/mistral-7b-instruct:free',
    label: 'Mistral 7B',
    description: 'Fast and capable model for general tasks',
    requiresSubscription: false,
    capabilities: ['text', 'chat']
  },
  { 
    id: 'openrouter/deepseek/deepseek-chat:free',
    label: 'DeepSeek Chat',
    description: 'Specialized for coding, technical tasks, and image analysis',
    requiresSubscription: true,
    capabilities: ['text', 'chat', 'code', 'image_analysis']
  },
  { 
    id: 'openrouter/meta-llama/llama-3.1-8b-instruct:free',
    label: 'Llama 3.1 8B',
    description: 'Balanced performance for general use',
    requiresSubscription: true,
    capabilities: ['text', 'chat']
  },
  { 
    id: 'openrouter/qwen/qwen3-235b-a22b:free',
    label: 'Qwen 3.5 72B',
    description: 'Most capable model for advanced tasks',
    requiresSubscription: true,
    capabilities: ['text', 'chat', 'reasoning']
  },
];
