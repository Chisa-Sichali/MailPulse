import React from 'react';
import AppSidebar from '@/components/AppSidebar';
import AuthGuard from '@/features/auth/AuthGuard';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return <AuthGuard><SidebarProvider><AppSidebar /><SidebarInset><div className="flex h-12 items-center border-b border-border/70 px-4 md:px-6"><SidebarTrigger /></div>{children}</SidebarInset></SidebarProvider></AuthGuard>;
}
