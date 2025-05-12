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
    // Clear any existing cached access status to force verification
    localStorage.removeItem('aiAccessStatus');
    localStorage.removeItem('aiAccessTimestamp');
    
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

        // IMPORTANT: For all non-admin users, always verify with the server
        // Don't trust the app_metadata or cached status for existing users

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
        
        // Use the backend URL directly to avoid 404 errors
        const backendUrl = 'https://defomai-backend-production.up.railway.app/api/check-ai-access';
        const response = await fetch(backendUrl, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        // If response is 200, user has access
        if (response.ok) {
          setHasAIAccess(true);
          localStorage.setItem('aiAccessStatus', 'true');
          localStorage.setItem('aiAccessTimestamp', now.toString());
          
          // Don't refresh the session to avoid rate limiting
          // Just update the local state
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

    // Always check access with the server for all users
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
