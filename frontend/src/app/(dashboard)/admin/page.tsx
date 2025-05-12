'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Copy,
  Check,
  RefreshCw,
  Shield,
  Key,
  Users,
  AlertCircle,
  Trash,
  Ban,
  Play,
} from 'lucide-react';
import { toast } from 'sonner';

// Type definitions
interface ActivationCode {
  id: string;
  code_value: string;
  is_active: boolean;
  created_at: string;
  is_claimed: boolean;
  claimed_at: string | null;
  notes: string | null;
  generated_by: string;
  claimed_by: string | null;
}

interface User {
  id: string;
  email: string;
  is_admin: boolean;
  has_ai_access: boolean;
  created_at: string;
  last_sign_in_at: string | null;
}

export default function AdminPanel() {
  const { user, supabase } = useAuth();
  const router = useRouter();
  const [activationCodes, setActivationCodes] = useState<ActivationCode[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [isLoadingCodes, setIsLoadingCodes] = useState(true);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('codes');
  const [isDeletingCode, setIsDeletingCode] = useState<string | null>(null);
  const [isSuspendingCode, setIsSuspendingCode] = useState<string | null>(null);
  const [isUnsuspendingCode, setIsUnsuspendingCode] = useState<string | null>(null);

  // Redirect non-admins
  useEffect(() => {
    if (user && !user.app_metadata?.is_admin) {
      router.push('/dashboard');
    }
  }, [user, router]);

  // Fetch activation codes
  const fetchActivationCodes = async () => {
    setIsLoadingCodes(true);
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/admin/activation-codes', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch activation codes');
      }

      const data = await response.json();
      if (data.success && data.codes) {
        setActivationCodes(data.codes);
      }
    } catch (error) {
      console.error('Error fetching activation codes:', error);
      toast.error('Failed to load activation codes');
    } finally {
      setIsLoadingCodes(false);
    }
  };

  // Fetch users
  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/admin/users', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      if (data.success && data.users) {
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setIsLoadingUsers(false);
    }
  };

  // Generate new activation code
  const generateActivationCode = async () => {
    setIsGeneratingCode(true);
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/admin/generate-code', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to generate activation code');
      }

      const data = await response.json();
      if (data.success && data.code) {
        toast.success('New activation code generated');
        fetchActivationCodes(); // Refresh the list
      }
    } catch (error) {
      console.error('Error generating activation code:', error);
      toast.error('Failed to generate activation code');
    } finally {
      setIsGeneratingCode(false);
    }
  };

  // Copy code to clipboard
  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeId(id);
    toast.success('Code copied to clipboard');
    setTimeout(() => setCopiedCodeId(null), 2000);
  };

  // Delete activation code
  const deleteActivationCode = async (codeId: string) => {
    setIsDeletingCode(codeId);
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/admin/activation-codes/${codeId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete activation code');
      }

      const data = await response.json();
      if (data.success) {
        toast.success('Activation code deleted successfully');
        fetchActivationCodes(); // Refresh the list
      }
    } catch (error) {
      console.error('Error deleting activation code:', error);
      toast.error('Failed to delete activation code');
    } finally {
      setIsDeletingCode(null);
    }
  };

  // Suspend or unsuspend activation code
  const toggleCodeSuspension = async (codeId: string, suspend: boolean) => {
    if (suspend) {
      setIsSuspendingCode(codeId);
    } else {
      setIsUnsuspendingCode(codeId);
    }

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/admin/activation-codes/${codeId}/suspend`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_suspended: suspend }),
      });

      if (!response.ok) {
        throw new Error(`Failed to ${suspend ? 'suspend' : 'unsuspend'} activation code`);
      }

      const data = await response.json();
      if (data.success) {
        toast.success(`Activation code ${suspend ? 'suspended' : 'unsuspended'} successfully`);
        fetchActivationCodes(); // Refresh the list
      }
    } catch (error) {
      console.error(`Error ${suspend ? 'suspending' : 'unsuspending'} activation code:`, error);
      toast.error(`Failed to ${suspend ? 'suspend' : 'unsuspend'} activation code`);
    } finally {
      if (suspend) {
        setIsSuspendingCode(null);
      } else {
        setIsUnsuspendingCode(null);
      }
    }
  };

  // Load data on component mount
  useEffect(() => {
    if (user && user.app_metadata?.is_admin) {
      if (activeTab === 'codes') {
        fetchActivationCodes();
      } else if (activeTab === 'users') {
        fetchUsers();
      }
    }
  }, [user, activeTab]);

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (!user || !user.app_metadata?.is_admin) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Access Restricted
            </CardTitle>
            <CardDescription>
              You need admin privileges to access this page.
            </CardDescription>
          </CardHeader>
          <CardFooter>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => router.push('/dashboard')}
            >
              Return to Dashboard
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Panel</h1>
          <p className="text-muted-foreground mt-1">
            Manage activation codes and users
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={() => {
              if (activeTab === 'codes') {
                fetchActivationCodes();
              } else if (activeTab === 'users') {
                fetchUsers();
              }
            }}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button
            size="sm"
            className="gap-1"
            onClick={generateActivationCode}
            disabled={isGeneratingCode}
          >
            <Key className="h-4 w-4" />
            {isGeneratingCode ? 'Generating...' : 'Generate New Code'}
          </Button>
        </div>
      </div>

      <Tabs
        defaultValue="codes"
        value={activeTab}
        onValueChange={setActiveTab}
        className="w-full"
      >
        <TabsList className="mb-6">
          <TabsTrigger value="codes" className="flex items-center gap-1">
            <Key className="h-4 w-4" />
            Activation Codes
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            Users
          </TabsTrigger>
        </TabsList>

        <TabsContent value="codes">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                AI Activation Codes
              </CardTitle>
              <CardDescription>
                Manage activation codes for AI feature access
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingCodes ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : activationCodes.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No activation codes found. Generate one to get started.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Code</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Claimed By</TableHead>
                        <TableHead>Claimed At</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {activationCodes.map((code) => (
                        <TableRow key={code.id}>
                          <TableCell className="font-mono">
                            {code.code_value}
                          </TableCell>
                          <TableCell>
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                code.is_claimed
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                  : code.is_active
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                              }`}
                            >
                              {code.is_claimed
                                ? 'Claimed'
                                : code.is_active
                                ? 'Active'
                                : 'Inactive'}
                            </span>
                          </TableCell>
                          <TableCell>
                            {formatDate(code.created_at)}
                          </TableCell>
                          <TableCell>
                            {code.claimed_by || 'Not claimed'}
                          </TableCell>
                          <TableCell>
                            {formatDate(code.claimed_at)}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  copyToClipboard(code.code_value, code.id)
                                }
                                disabled={code.is_claimed}
                                title="Copy code"
                              >
                                {copiedCodeId === code.id ? (
                                  <Check className="h-4 w-4" />
                                ) : (
                                  <Copy className="h-4 w-4" />
                                )}
                              </Button>
                              
                              {/* Suspend/Unsuspend button */}
                              {code.is_active ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleCodeSuspension(code.id, true)}
                                  className="text-amber-500 hover:text-amber-600 hover:bg-amber-100 dark:hover:bg-amber-900/20"
                                  disabled={isSuspendingCode === code.id}
                                  title="Suspend code"
                                >
                                  {isSuspendingCode === code.id ? (
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Ban className="h-4 w-4" />
                                  )}
                                </Button>
                              ) : (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleCodeSuspension(code.id, false)}
                                  className="text-green-500 hover:text-green-600 hover:bg-green-100 dark:hover:bg-green-900/20"
                                  disabled={isUnsuspendingCode === code.id}
                                  title="Unsuspend code"
                                >
                                  {isUnsuspendingCode === code.id ? (
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Play className="h-4 w-4" />
                                  )}
                                </Button>
                              )}
                              
                              {/* Delete button */}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => deleteActivationCode(code.id)}
                                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                disabled={isDeletingCode === code.id}
                                title="Delete code"
                              >
                                {isDeletingCode === code.id ? (
                                  <RefreshCw className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash className="h-4 w-4" />
                                )}
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                User Management
              </CardTitle>
              <CardDescription>
                View and manage user accounts and permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingUsers ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No users found.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Email</TableHead>
                        <TableHead>Admin</TableHead>
                        <TableHead>AI Access</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Last Sign In</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            {user.is_admin ? (
                              <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900 dark:text-purple-300">
                                <Shield className="mr-1 h-3 w-3" />
                                Admin
                              </span>
                            ) : (
                              'No'
                            )}
                          </TableCell>
                          <TableCell>
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                user.has_ai_access
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                              }`}
                            >
                              {user.has_ai_access ? 'Yes' : 'No'}
                            </span>
                          </TableCell>
                          <TableCell>
                            {formatDate(user.created_at)}
                          </TableCell>
                          <TableCell>
                            {formatDate(user.last_sign_in_at)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
