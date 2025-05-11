'use client';

import { useAuth } from '@/components/AuthProvider';
import { SidebarMenuItem } from '@/components/ui/sidebar';
import { Shield } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function AdminNavItem() {
  const { user } = useAuth();
  const pathname = usePathname();
  const isActive = pathname === '/admin';

  // Only show for admin users
  if (!user?.app_metadata?.is_admin) {
    return null;
  }

  return (
    <Link href="/admin" className="block w-full">
      <SidebarMenuItem data-active={isActive}>
        <Shield className="h-4 w-4 mr-2" />
        Admin Panel
      </SidebarMenuItem>
    </Link>
  );
}
