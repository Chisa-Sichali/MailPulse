"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarMenu,
  SidebarMenuItem,
  SidebarHeader,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Separator } from "@/components/ui/separator";
import { SidebarLinks } from "@/utils/data/sidebar-data";
import { Mail } from "lucide-react";

export default function AppSidebar() {
  const pathname = usePathname();
  const currentPath = pathname?.split("/")[1] || "";

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
    </Sidebar>
  );
}
