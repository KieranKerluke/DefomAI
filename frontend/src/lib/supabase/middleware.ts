import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { type NextRequest, NextResponse } from 'next/server';

function forceLoginWithReturn(request: NextRequest) {
  const originalUrl = new URL(request.url);
  const path = originalUrl.pathname;
  const query = originalUrl.searchParams.toString();
  return NextResponse.redirect(
    new URL(
      `/auth?returnUrl=${encodeURIComponent(path + (query ? `?${query}` : ''))}`,
      request.url,
    ),
  );
}

export const validateSession = async (request: NextRequest) => {
  // Temporarily bypass authentication
  return NextResponse.next({
    request: {
      headers: request.headers,
    },
  });
};
