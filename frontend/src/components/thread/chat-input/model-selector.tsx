'use client';

import React, { useMemo } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { Check, ChevronDown, Lock, Unlock, Star, BarChart3, Image } from 'lucide-react';
import { ModelOption } from '@/types/model';
import { cn } from '@/lib/utils';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  modelOptions: ModelOption[];
  canAccessModel: (modelId: string) => boolean;
  isLocked: boolean;
  onToggleLock: () => void;
  className?: string;
  taskType?: string;
  confidence?: number;
  useUserSelection?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange,
  modelOptions,
  canAccessModel,
  isLocked,
  onToggleLock,
  className,
  taskType,
  confidence,
  useUserSelection,
}) => {
  const selectedModelData = useMemo(
    () => modelOptions.find((m) => m.id === selectedModel),
    [modelOptions, selectedModel]
  );

  const handleSelect = (id: string) => {
    if (canAccessModel(id)) {
      onModelChange(id);
    }
  };

  const getPerformanceColor = (rate?: number) => {
    if (!rate) return 'text-muted-foreground';
    if (rate >= 0.9) return 'text-green-500';
    if (rate >= 0.7) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className={cn('relative', className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 rounded-md text-foreground/80 hover:text-foreground hover:bg-accent/50"
          >
            <div className="flex items-center gap-2 text-sm font-medium">
              <div className="flex items-center gap-1.5">
                {selectedModelData?.performance?.rank === 1 && (
                  <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                )}
                <span>{selectedModelData?.label || 'Select model'}</span>
                {isLocked ? (
                  <Lock className="h-3 w-3 text-muted-foreground" />
                ) : (
                  <BarChart3 className="h-3 w-3 text-muted-foreground" />
                )}
              </div>
              <ChevronDown className="h-3.5 w-3.5 opacity-70" />
            </div>
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-80 p-2 space-y-1">
          <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground flex justify-between items-center">
            <span>AI Model</span>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleLock();
                    }}
                  >
                    {isLocked ? (
                      <Lock className="h-3.5 w-3.5" />
                    ) : (
                      <Unlock className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left">
                  {isLocked ? 'Unlock model selection' : 'Lock model selection'}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          
          <DropdownMenuSeparator className="my-1" />
          
          {modelOptions.map((opt) => {
            const accessible = canAccessModel(opt.id);
            const isSelected = selectedModel === opt.id;
            const isTopPerformer = opt.performance?.rank === 1;
            
            return (
              <TooltipProvider key={opt.id}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <DropdownMenuItem
                      className={cn(
                        'py-2 px-3 rounded-md text-sm',
                        isSelected 
                          ? 'bg-accent/50 font-medium' 
                          : 'hover:bg-accent/30',
                        !accessible && 'opacity-60 cursor-not-allowed'
                      )}
                      onClick={() => handleSelect(opt.id)}
                      disabled={!accessible}
                    >
                      <div className="flex flex-col w-full gap-1">
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center gap-2">
                            {isTopPerformer && (
                              <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                            )}
                            {opt.capabilities?.includes('image_analysis') && (
                              <Image className="h-3.5 w-3.5 text-blue-500" />
                            )}
                            <span className={cn(
                              'font-medium',
                              isTopPerformer && 'text-yellow-500'
                            )}>
                              {opt.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {opt.performance?.successRate !== undefined && (
                              <span className={cn(
                                'text-xs',
                                getPerformanceColor(opt.performance.successRate)
                              )}>
                                {Math.round(opt.performance.successRate * 100)}%
                              </span>
                            )}
                            {isSelected && (
                              <Check className="h-3.5 w-3.5 text-primary" />
                            )}
                          </div>
                        </div>
                        
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {opt.description}
                        </div>
                        
                        {opt.capabilities && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {opt.capabilities.includes('image_analysis') && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                                <Image className="h-2 w-2 mr-1" /> Image Analysis
                              </span>
                            )}
                            {opt.capabilities.includes('code') && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300">
                                Code
                              </span>
                            )}
                          </div>
                        )}
                        
                        {opt.performance && (
                          <div className="mt-1 flex items-center gap-2 text-[10px] text-muted-foreground">
                            {opt.performance.rank && (
                              <span className="flex items-center gap-0.5">
                                <BarChart3 className="h-2.5 w-2.5" />
                                #{opt.performance.rank}
                              </span>
                            )}
                            {opt.performance.taskSuccessRate !== undefined && (
                              <span className={cn(
                                'flex items-center gap-0.5',
                                getPerformanceColor(opt.performance.taskSuccessRate)
                              )}>
                                Task: {Math.round(opt.performance.taskSuccessRate * 100)}%
                              </span>
                            )}
                            <span className="text-muted-foreground/60">
                              • {opt.performance.totalRequests?.toLocaleString()} requests
                            </span>
                          </div>
                        )}
                      </div>
                    </DropdownMenuItem>
                  </TooltipTrigger>
                  {!accessible && (
                    <TooltipContent side="left" className="text-xs">
                      Upgrade to access this model
                    </TooltipContent>
                  )}
                </Tooltip>
              </TooltipProvider>
            );
          })}
          
          <DropdownMenuSeparator className="my-1" />
          
          <div className="px-2 py-1.5">
            <p className="text-xs text-muted-foreground">
              {isLocked 
                ? 'Model selection is locked. The system will always use your selected model.'
                : 'The system will automatically select the best model for each task.'}
            </p>
            
            {taskType && !isLocked && (
              <div className="mt-1 flex flex-col gap-1">
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium">Detected task:</span> {taskType}
                  {confidence !== undefined && (
                    <span className="ml-1 text-xs opacity-70">
                      (confidence: {Math.round(confidence * 100)}%)
                    </span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {useUserSelection 
                    ? 'Using your preferred model for this task.' 
                    : 'AI selected the optimal model for this task type.'}
                </p>
              </div>
            )}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};