'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import ActivateAIForm from './ActivateAIForm';
import { Loader2 } from 'lucide-react';

interface AIAccessCheckProps {
  children: ReactNode;
}

export default function AIAccessCheck({ children }: AIAccessCheckProps) {
  const { user, supabase } = useAuth();
  const [hasAIAccess, setHasAIAccess] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for cached access status to reduce API calls
    const cachedAccessStatus = localStorage.getItem('aiAccessStatus');
    const cachedTimestamp = localStorage.getItem('aiAccessTimestamp');
    const now = Date.now();
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
    
    // Function to check AI access
    const checkAIAccess = async () => {
      if (!user) {
        setIsLoading(false);
        return;
      }

      try {
        // First check if user is admin, admins always have access
        if (user.app_metadata?.is_admin) {
          setHasAIAccess(true);
          localStorage.setItem('aiAccessStatus', 'true');
          localStorage.setItem('aiAccessTimestamp', now.toString());
          setIsLoading(false);
          return;
        }

        // Check if user has AI access in app_metadata
        if (user.app_metadata?.has_ai_access) {
          // Even if metadata says they have access, we'll still verify with the server
          // but less frequently to avoid rate limiting
          if (cachedAccessStatus === 'true' && cachedTimestamp && 
              (now - parseInt(cachedTimestamp)) < CACHE_DURATION) {
            setHasAIAccess(true);
            setIsLoading(false);
            return;
          }
        }

        // If we need to check with the server
        const { data: sessionData } = await supabase.auth.getSession();
        const token = sessionData.session?.access_token;

        if (!token) {
          setHasAIAccess(false);
          localStorage.setItem('aiAccessStatus', 'false');
          localStorage.setItem('aiAccessTimestamp', now.toString());
          setIsLoading(false);
          return;
        }

        // Add a small delay to prevent rapid API calls
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Make a request to check AI access
        const response = await fetch('/api/check-ai-access', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        // If response is 200, user has access
        if (response.ok) {
          setHasAIAccess(true);
          localStorage.setItem('aiAccessStatus', 'true');
          localStorage.setItem('aiAccessTimestamp', now.toString());
          
          // Update local session metadata for future checks
          await supabase.auth.refreshSession();
        } else {
          setHasAIAccess(false);
          localStorage.setItem('aiAccessStatus', 'false');
          localStorage.setItem('aiAccessTimestamp', now.toString());
        }
      } catch (error) {
        console.error('Error checking AI access:', error);
        setHasAIAccess(false);
      } finally {
        setIsLoading(false);
      }
    };

    // Use cached value if available and recent
    if (cachedAccessStatus && cachedTimestamp && 
        (now - parseInt(cachedTimestamp)) < CACHE_DURATION) {
      setHasAIAccess(cachedAccessStatus === 'true');
      setIsLoading(false);
    } else {
      checkAIAccess();
    }
  }, [user, supabase]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // If user has AI access or is admin, show the children
  if (hasAIAccess) {
    return <>{children}</>;
  }

  // Otherwise show the activation form
  return (
    <div className="container mx-auto py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Activate AI Access</h1>
        <p className="text-muted-foreground text-center mb-8">
          You need to activate AI access to use this feature. Please enter your activation code below.
        </p>
        <ActivateAIForm />
      </div>
    </div>
  );
}
