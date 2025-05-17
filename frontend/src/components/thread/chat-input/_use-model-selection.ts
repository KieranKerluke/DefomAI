'use client';

import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { useLocalStorage } from 'usehooks-ts';
import { ModelSuggestionResponse, ModelOption, DEFAULT_MODEL, MODEL_OPTIONS } from '@/types/model';

// Mock API client
const apiClient = {
  post: async <T,>(
    url: string, 
    data: any
  ): Promise<{ data: T }> => {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error('API request failed');
    }
    
    return response.json();
  },
};

type SubscriptionStatus = 'active' | 'inactive' | 'trial' | 'expired' | 'canceled';

interface AuthContextType {
  user: any;
  subscription: {
    status: SubscriptionStatus;
    [key: string]: any;
  } | null;
}

// Mock auth context
export const useAuth = (): AuthContextType => ({
  user: null,
  subscription: { status: 'active' },
});

export const useModelSelection = () => {
  const { subscription } = useAuth();
  const [preferredModel, setPreferredModel] = useLocalStorage<string>(
    'suna-preferred-model',
    DEFAULT_MODEL
  );
  const [isLocked, setIsLocked] = useLocalStorage<boolean>('suna-model-locked', false);
  const [selectedModel, setSelectedModel] = useState<string>(DEFAULT_MODEL);
  const [availableModels, setAvailableModels] = useState<ModelOption[]>(MODEL_OPTIONS);

  // Check if user can access a specific model
  const canAccessModel = useCallback((modelId: string) => {
    const model = availableModels.find(m => m.id === modelId);
    if (!model) return false;
    
    // Free models are always accessible
    if (!model.requiresSubscription) return true;
    
    // Check subscription status for premium models
    return subscription?.status === 'active';
  }, [availableModels, subscription]);

  // Helper function to detect if prompt contains image-related content
  const detectImageContent = (prompt: string): boolean => {
    const imageRelatedTerms = [
      'image', 'picture', 'photo', 'screenshot', 'scan', 'ocr', 
      'analyze image', 'image analysis', 'what is in this image',
      'describe this image', 'what do you see', 'visual', 'camera',
      'recognize', 'detect objects', 'image shows', 'in the picture'
    ];
    
    const promptLower = prompt.toLowerCase();
    return imageRelatedTerms.some(term => promptLower.includes(term));
  };

  // Get model suggestion from the backend following the hybrid approach
  const getModelSuggestion = useCallback(async (prompt: string) => {
    try {
      // Check if this is an image-related task
      const isImageTask = detectImageContent(prompt);
      
      // If this is an image task and not locked, prioritize DeepSeek
      let suggestedModelForTask = '';
      if (isImageTask && !isLocked) {
        const deepseekModel = availableModels.find(m => 
          m.capabilities?.includes('image_analysis') && canAccessModel(m.id)
        );
        if (deepseekModel) {
          suggestedModelForTask = deepseekModel.id;
        }
      }

      // Align with the proposed API format in the plan
      const response = await apiClient.post<ModelSuggestionResponse>('/api/model/suggest', {
        prompt,
        userSelectedModel: isLocked ? selectedModel : preferredModel,
        isLocked,
        suggestedModelForTask // Pass our suggestion to the backend
      });
      
      // Update model options with performance data
      const updatedModels = availableModels.map(model => ({
        ...model,
        performance: response.data.ranked_models?.find(m => m.model_id === model.id)?.performance,
      }));
      
      setAvailableModels(updatedModels);
      
      // For image tasks, prioritize DeepSeek if available and not locked
      let modelToUse = isLocked ? selectedModel : response.data.suggested_model;
      
      // If this is an image task and we have a DeepSeek model, use it (unless locked)
      if (isImageTask && !isLocked && suggestedModelForTask) {
        modelToUse = suggestedModelForTask;
      }
      
      // If not locked and the suggested model is different, update the UI
      if (!isLocked && modelToUse !== selectedModel) {
        setSelectedModel(modelToUse);
      }
      
      return {
        suggestedModel: modelToUse,
        useUserSelection: isLocked,
        taskType: isImageTask ? 'image_analysis' : response.data.task_type,
        confidence: response.data.confidence,
        models: updatedModels,
      };
    } catch (error) {
      console.error('Error getting model suggestion:', error);
      return {
        suggestedModel: selectedModel,
        useUserSelection: true,
        models: availableModels,
      };
    }
  }, [availableModels, isLocked, preferredModel, selectedModel, canAccessModel]);

  // Update selected model when preferred model changes
  useEffect(() => {
    if (preferredModel && canAccessModel(preferredModel)) {
      setSelectedModel(preferredModel);
    } else {
      // Fallback to default model if preferred model is not accessible
      const defaultModel = availableModels.find(m => !m.requiresSubscription)?.id || DEFAULT_MODEL;
      setSelectedModel(defaultModel);
      if (preferredModel !== defaultModel) {
        setPreferredModel(defaultModel);
      }
    }
  }, [preferredModel, canAccessModel, availableModels, setPreferredModel]);

  // Handle model selection
  const handleModelChange = useCallback((modelId: string) => {
    if (canAccessModel(modelId)) {
      setSelectedModel(modelId);
      setPreferredModel(modelId);
    }
  }, [canAccessModel, setPreferredModel]);

  // Toggle model lock
  const toggleModelLock = useCallback(() => {
    setIsLocked(prev => !prev);
  }, [setIsLocked]);

  // Use the useQuery hook with proper typing
  const { data: modelSuggestion, isLoading } = useQuery<{
    suggestedModel: string;
    models: ModelOption[];
    taskType?: string;
    confidence?: number;
    useUserSelection?: boolean;
  }>({
    queryKey: ['modelSuggestion', selectedModel, isLocked],
    queryFn: () => getModelSuggestion(''),
    staleTime: 60000,
    refetchOnWindowFocus: false,
  });

  // Update available models when suggestions are received
  useEffect(() => {
    if (modelSuggestion?.models) {
      setAvailableModels(modelSuggestion.models);
    }
  }, [modelSuggestion]);

  return {
    selectedModel,
    setSelectedModel: handleModelChange,
    modelOptions: availableModels,
    canAccessModel,
    isLocked,
    toggleModelLock,
    getModelSuggestion,
    isLoading,
    taskType: modelSuggestion?.taskType,
    confidence: modelSuggestion?.confidence,
    useUserSelection: modelSuggestion?.useUserSelection || isLocked,
  };
};