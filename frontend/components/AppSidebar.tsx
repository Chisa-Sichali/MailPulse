"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarHeader,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Separator } from "@/components/ui/separator";
import { SidebarLinks } from "@/utils/data/sidebar-data";
import { ChevronUp, Mail, UserRound } from "lucide-react";
import { DarkModeSwitcher } from "@/components/DarkModeSwitcher";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth";
import { removeTokens } from "@/utils/auth-utils";
import { useRouter } from "next/navigation";
import { toast } from "@/components/ui/toast";
import { useDashboardStore } from "@/stores/dashboard.store";

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const clearDashboardState = useDashboardStore((state) => state.clearOverviewData);
  const profile = useQuery({ queryKey: ['currentUser'], queryFn: authService.GetCurrentUser, staleTime: 5 * 60_000 });
  const currentPath = pathname?.split("/")[1] || "";
  const logout = useMutation({
    mutationFn: authService.Logout,
    onSettled: (_data, error) => {
      removeTokens();
      queryClient.clear();
      clearDashboardState();
      router.replace('/');
      if (error) toast.add({ title: 'Signed out locally', description: 'The server could not be reached to revoke this session.', type: 'warning' });
    },
  });

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center p-2 mb-2 gap-2">
          <div className="flex items-center justify-center rounded-lg bg-linear-to-r from-[#6366f1] to-[#8b5cf6] p-2">
            <Mail size={20} className="text-white" />
          </div>
          <div className="flex flex-col justify-center">
            <h1 className="text-lg font-semibold text-primary">MailPulse</h1>
            <span className="text-xs text-muted-foreground">
              Email event platform
            </span>
          </div>
        </div>
        <Separator />
      </SidebarHeader>
      <SidebarContent className="px-2.5">
        <SidebarMenu className="gap-0.5">
          {SidebarLinks.map((link) => (
            <SidebarMenuItem key={link.name}>
              {link.name === "System" && <Separator className="my-2" />}
              <SidebarMenuButton
                render={<Link href={link.href} />}
                className={`h-9 gap-2.5 rounded-lg px-3 ${currentPath === link.href.split("/")[1] ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"}`}
              >
                {link.icon}
                <span>{link.name}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border p-2">
        <details className="group relative">
          <summary className="flex cursor-pointer list-none items-center gap-2 rounded-md px-2 py-2 hover:bg-sidebar-accent [&::-webkit-details-marker]:hidden">
            <span className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-primary"><UserRound className="size-4" /></span>
            <span className="min-w-0 flex-1 text-left"><span className="block truncate text-sm font-medium">{profile.data?.full_name || 'Account'}</span><span className="block truncate text-xs text-muted-foreground">{profile.data?.email || 'Loading profile…'}</span></span>
            <ChevronUp className="size-4 text-muted-foreground transition-transform group-open:rotate-180" />
          </summary>
          <div className="absolute right-0 bottom-full left-0 z-30 mb-2 rounded-lg border border-sidebar-border bg-popover p-2 shadow-lg">
            <div className="flex items-center justify-between px-2 py-1.5 text-xs text-muted-foreground"><span>Appearance</span><DarkModeSwitcher /></div>
            <Separator className="my-1" />
            <Button className="w-full justify-start" variant="ghost" disabled={logout.isPending} onClick={() => logout.mutate()}><LogOut />{logout.isPending ? 'Signing out…' : 'Sign out'}</Button>
          </div>
        </details>
      </SidebarFooter>
    </Sidebar>
  );
}
