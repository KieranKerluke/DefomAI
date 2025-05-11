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
    const checkAIAccess = async () => {
      if (!user) {
        setIsLoading(false);
        return;
      }

      try {
        // First check if user is admin, admins always have access
        if (user.app_metadata?.is_admin) {
          setHasAIAccess(true);
          setIsLoading(false);
          return;
        }

        // Check if user has AI access in app_metadata
        if (user.app_metadata?.has_ai_access) {
          setHasAIAccess(true);
          setIsLoading(false);
          return;
        }

        // If not in app_metadata, check with the server
        const { data: sessionData } = await supabase.auth.getSession();
        const token = sessionData.session?.access_token;

        if (!token) {
          setHasAIAccess(false);
          setIsLoading(false);
          return;
        }

        // Make a request to a simple endpoint that requires AI access
        // This will use the ai_access_required middleware
        const response = await fetch('/api/check-ai-access', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        // If response is 200, user has access
        if (response.ok) {
          setHasAIAccess(true);
          
          // Update local session metadata for future checks
          await supabase.auth.refreshSession();
        } else {
          setHasAIAccess(false);
        }
      } catch (error) {
        console.error('Error checking AI access:', error);
        setHasAIAccess(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAIAccess();
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
