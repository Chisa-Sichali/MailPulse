import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export default function DashboardHeaderLoader() {
  return (
    <Card className="w-full overflow-hidden border-0 bg-linear-to-r from-[#6366f1] to-[#8b5cf6] text-white shadow-lg">
      <div className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:gap-6 md:p-6">
        {/* Status Loader */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <Skeleton className="size-2.5 shrink-0 rounded-full bg-white/25" />
          <div className="min-w-0 flex-1">
            <Skeleton className="h-4 w-40 bg-white/25" />
            <Skeleton className="mt-2 h-3 w-56 bg-white/25" />
          </div>
        </div>

        {/* More info Loader */}
        <Skeleton className="h-4 w-32 self-start md:self-center bg-white/25" />

        {/* Connection state Loader */}
        <Skeleton className="h-8 w-24 rounded-full self-start md:self-center bg-white/25" />
      </div>
    </Card>
  );
}
