import {
  Activity,
  ChartNoAxesCombined,
  Home,
  Mail,
  Settings2,
  Webhook,
} from "lucide-react";
export const SidebarLinks = [
  {
    name: "Overview",
    href: "/dashboard",
    icon: <Home className="w-5 h-5" />,
  },
  {
    name: "Mailboxes",
    href: "/mailboxes",
    icon: <Mail className="w-5 h-5" />,
  },
  {
    name: "Webhooks",
    href: "/webhooks",
    icon: <Webhook className="w-5 h-5" />,
  },
  {
    name: "Events",
    href: "/events",
    icon: <Activity className="w-5 h-5" />,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: <ChartNoAxesCombined className="w-5 h-5" />,
  },
  {
    name: "System",
    href: "/system",
    icon: <Settings2 className="w-5 h-5" />,
  },
];
