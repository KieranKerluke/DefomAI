'use server';
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';

export const createClient = async () => {
  const cookieStore = await cookies();
  const supabaseUrl = 'https://dxclumbzndzxztkounbw.supabase.co';
  const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4Y2x1bWJ6bmR6eHp0a291bmJ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY1NzYzODAsImV4cCI6MjA2MjE1MjM4MH0.HfliizteRVoBVASO9MD0_RT2pdZWRqImIywsWMjOMes';

  try {
    return createServerClient(supabaseUrl, supabaseAnonKey, {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set({ name, value, ...options }),
            );
          } catch (error) {
            console.error('Error setting cookies:', error);
            // The `set` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    });
  } catch (error) {
    console.error('Error creating Supabase server client:', error);
    throw error;
  }
};
