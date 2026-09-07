'use client';

import DashboardHeader from '@/features/dashboard/DashboardHeader';
import { useDashboardStore } from '@/stores/dashboard.store';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import DashboardStats from '@/features/dashboard/DashboardStats';
import { EmailVolumeChart } from '@/features/dashboard/EmailVolumeChart';
import { DashboardTables } from '@/features/dashboard/DashboardTables';

const FILTER_ITEMS = [
  { value: 7, label: '7 Days' },
  { value: 14, label: '14 Days' },
  { value: 30, label: '30 Days' },
  { value: 90, label: '90 Days' },
];

export default function DashboardPage() {
  const daysFilter = useDashboardStore((state) => state.daysFilter);
  const setDaysFilter = useDashboardStore((state) => state.setDaysFilter);

  return (
    <main className="bg-background flex flex-1 flex-col px-4 py-4 md:px-6 md:py-5">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold tracking-[0.14em] text-primary uppercase">Operations console</p>
            <h1 className="text-xl font-semibold tracking-tight">Email infrastructure overview</h1>
            <span className="text-muted-foreground text-sm">
              Monitor email processing and webhook delivery at a glance.
            </span>
          </div>
          <div className="flex w-full shrink-0 items-center sm:w-auto">
            <Select
              value={daysFilter}
              onValueChange={(val) => {
                if (val !== null) setDaysFilter(val);
              }}
              items={FILTER_ITEMS}
            >
              <SelectTrigger className="w-full text-sm font-medium sm:w-[130px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FILTER_ITEMS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DashboardHeader />
        <DashboardStats />
        <EmailVolumeChart days={daysFilter} />
        <DashboardTables days={daysFilter} />
      </div>
    </main>
  );
}
