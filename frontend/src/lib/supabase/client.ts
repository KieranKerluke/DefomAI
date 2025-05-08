import { createBrowserClient } from '@supabase/ssr';

export const createClient = () => {
  const supabaseUrl = 'https://dxclumbzndzxztkounbw.supabase.co';
  const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4Y2x1bWJ6bmR6eHp0a291bmJ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY1NzYzODAsImV4cCI6MjA2MjE1MjM4MH0.HfliizteRVoBVASO9MD0_RT2pdZWRqImIywsWMjOMes';

  try {
    return createBrowserClient(supabaseUrl, supabaseAnonKey);
  } catch (error) {
    console.error('Error creating Supabase client:', error);
    throw error;
  }
};
