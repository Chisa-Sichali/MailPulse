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
    <main className="bg-background flex flex-1 flex-col px-4 py-2 md:py-4">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold text-gray-900">Overview</h1>
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
      </div>
    </main>
  );
}
