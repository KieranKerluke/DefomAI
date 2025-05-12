'use client';

import { useState } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Key, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function ActivateAIForm() {
  const { user, supabase } = useAuth();
  const [code, setCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const activateAI = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      // Use the backend URL directly to avoid 404 errors
      const backendUrl = 'https://defomai-backend-production.up.railway.app/api/activate-ai';
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
        toast.success('AI access activated successfully!');
        
        // Refresh the user session to update metadata
        await supabase.auth.refreshSession();
        
        // Reload the page after a short delay to reflect the changes
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        setError(data.message || 'Failed to activate AI access');
        toast.error(data.message || 'Failed to activate AI access');
      }
    } catch (error) {
      console.error('Error activating AI access:', error);
      setError('An error occurred. Please try again.');
      toast.error('An error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5" />
          Activate AI Access
        </CardTitle>
        <CardDescription>
          Enter your activation code to unlock AI features
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {success ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="rounded-full bg-green-100 p-3 dark:bg-green-900 mb-4">
              <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-300" />
            </div>
            <h3 className="text-xl font-medium mb-2">Activation Successful!</h3>
            <p className="text-muted-foreground">
              Your AI access has been activated. The page will refresh momentarily.
            </p>
            <div className="mt-4">
              <Loader2 className="h-5 w-5 animate-spin mx-auto" />
            </div>
          </div>
        ) : (
          <form onSubmit={activateAI}>
            <div className="space-y-4">
              <div className="space-y-2">
                <label
                  htmlFor="activation-code"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Activation Code
                </label>
                <Input
                  id="activation-code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Enter your activation code"
                  className="font-mono"
                  required
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-md bg-destructive/15 px-3 py-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <Button
              type="submit"
              className="w-full mt-6"
              disabled={isSubmitting || !code}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Activating...
                </>
              ) : (
                'Activate AI Access'
              )}
            </Button>
          </form>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-center border-t pt-4">
        <p className="text-xs text-muted-foreground text-center">
          Don't have an activation code? Contact your administrator to get one.
        </p>
      </CardFooter>
    </Card>
  );
}
