"use client";

import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { healthService } from "@/services/health";

export function EmailVolumeChart({ days }: { days: number }) {
  const query = useQuery({
    queryKey: ["emailVolume", days],
    queryFn: () => healthService.getVolume(days),
    staleTime: 20_000,
    refetchInterval: 60_000,
  });
  const data = query.data ?? [];

  return (
    <Card className="min-h-[330px] border-border/80 shadow-sm">
      <CardHeader className="border-b border-border/70 pb-4">
        <CardTitle className="text-sm font-semibold">Email volume</CardTitle>
        <CardDescription>Processed messages by day over the selected period.</CardDescription>
      </CardHeader>
      <CardContent className="h-[255px] px-3 pb-3 pt-5 sm:px-5">
        {query.isPending ? <Skeleton className="h-full w-full" /> : query.isError ? (
          <ChartMessage message="Email volume is temporarily unavailable." />
        ) : data.length === 0 ? (
          <ChartMessage message="No email activity recorded for this period." />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
              <defs><linearGradient id="volumeFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.3} /><stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0.02} /></linearGradient></defs>
              <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(value: string) => new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(`${value}T00:00:00`))} tickLine={false} axisLine={false} minTickGap={28} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: "8px", color: "var(--popover-foreground)", fontSize: "12px" }} labelFormatter={(value) => typeof value === "string" ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`)) : value} />
              <Area type="monotone" dataKey="count" name="Emails" stroke="var(--chart-1)" strokeWidth={2} fill="url(#volumeFill)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

function ChartMessage({ message }: { message: string }) {
  return <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 px-4 text-center text-sm text-muted-foreground">{message}</div>;
}
