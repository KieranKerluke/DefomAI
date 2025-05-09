'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { createProject, createThread } from '@/lib/api';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      toast.error('Please provide a name for your agent');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Create a new project
      const project = await createProject({
        name,
        description,
      });
      
      // Create a thread for this project
      const thread = await createThread(project.id);
      
      // Redirect to the new thread
      toast.success('Agent created successfully');
      router.push(`/agents/${thread.thread_id}`);
    } catch (error) {
      console.error('Error creating agent:', error);
      toast.error(
        error instanceof Error 
          ? error.message 
          : 'An error occurred while creating the agent'
      );
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="container mx-auto py-6 max-w-2xl">
      <div className="mb-6">
        <Button variant="ghost" asChild className="mb-4">
          <Link href="/agents">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Agents
          </Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Create New Agent</h1>
        <p className="text-muted-foreground mt-2">
          Set up a new AI agent to help with your tasks
        </p>
      </div>
      
      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Agent Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Name
              </label>
              <Input
                id="name"
                placeholder="Enter agent name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                Description (optional)
              </label>
              <Textarea
                id="description"
                placeholder="Describe what this agent does"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
              />
            </div>
          </CardContent>
          <CardFooter className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              type="button"
              onClick={() => router.push('/agents')}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting || !name.trim()}
            >
              {isSubmitting ? 'Creating...' : 'Create Agent'}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
