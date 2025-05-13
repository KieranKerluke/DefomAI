'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import ActivateAIForm from './ActivateAIForm';
import { Loader2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface AIAccessCheckProps {
  children: ReactNode;
}

interface AIAccessStatus {
  has_access: boolean;
  is_suspended: boolean;
  is_blocked: boolean;
  message: string;
  status: 'active' | 'suspended' | 'blocked' | 'no_access' | 'unauthenticated' | 'admin';
  code?: string;
}

export default function AIAccessCheck({ children }: AIAccessCheckProps) {
  const { user, supabase } = useAuth();
  const [hasAIAccess, setHasAIAccess] = useState<boolean | null>(null);
  const [accessStatus, setAccessStatus] = useState<AIAccessStatus | null>(null);
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

        if (response.ok) {
          const data = await response.json() as AIAccessStatus;
          setAccessStatus(data);
          setHasAIAccess(data.has_access);
          
          // Store the access status in localStorage
          localStorage.setItem('aiAccessStatus', data.has_access ? 'true' : 'false');
          localStorage.setItem('aiAccessTimestamp', now.toString());
        } else {
          setHasAIAccess(false);
          setAccessStatus(null);
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

  // Display appropriate message based on access status
  return (
    <div className="container mx-auto py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {accessStatus?.is_blocked ? (
          <>
            <h1 className="text-3xl font-bold mb-8 text-center">Access Blocked</h1>
            <Alert variant="destructive" className="mb-8">
              <ShieldAlert className="h-4 w-4" />
              <AlertTitle>Access Blocked</AlertTitle>
              <AlertDescription>
                {accessStatus.message || "Your access has been blocked by an administrator. Please contact support for assistance."}
              </AlertDescription>
            </Alert>
          </>
        ) : accessStatus?.is_suspended ? (
          <>
            <h1 className="text-3xl font-bold mb-8 text-center">Access Suspended</h1>
            <Alert variant="default" className="mb-8 border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 dark:border-yellow-800">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Access Suspended</AlertTitle>
              <AlertDescription>
                {accessStatus.message || "Your access has been temporarily suspended. Please contact support for assistance."}
              </AlertDescription>
            </Alert>
          </>
        ) : (
          <>
            <h1 className="text-3xl font-bold mb-8 text-center">Activate AI Access</h1>
            <p className="text-muted-foreground text-center mb-8">
              {accessStatus?.message || "You need to activate AI access to use this feature. Please enter your activation code below."}
            </p>
            <ActivateAIForm />
          </>
        )}
      </div>
    </div>
  );
}
