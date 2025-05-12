'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import ActivateAIForm from './ActivateAIForm';
import { Loader2 } from 'lucide-react';

interface DashboardActivationProps {
  children: ReactNode;
}

export default function DashboardActivation({ children }: DashboardActivationProps) {
  const { user, supabase } = useAuth();
  const [hasAIAccess, setHasAIAccess] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Always clear any cached access status to ensure proper verification
    localStorage.removeItem('aiAccessStatus');
    localStorage.removeItem('aiAccessTimestamp');
    
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

        // Always verify with the server for non-admin users
        const { data: sessionData } = await supabase.auth.getSession();
        const token = sessionData.session?.access_token;

        if (!token) {
          setHasAIAccess(false);
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
          const data = await response.json();
          setHasAIAccess(data.has_access === true);
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

  // Otherwise show the activation form prominently on the dashboard
  return (
    <div className="container mx-auto py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-4 text-center">Welcome to Suna AI</h1>
        <p className="text-muted-foreground text-center mb-8">
          To access the AI features, please enter your activation code below.
        </p>
        <div className="bg-card rounded-lg border shadow-sm p-6">
          <ActivateAIForm />
        </div>
      </div>
    </div>
  );
}
