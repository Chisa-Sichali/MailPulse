import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export default function DashboardStatsLoader() {
  return (
    <>
      {Array.from({ length: 4 }, (_, i) => (
        <Card key={i} className="bg-card text-card-foreground border shadow-xs">
          <CardContent className="flex flex-col gap-1.5 p-5">
            <Skeleton className="h-3 w-[100px]" />
            <Skeleton className="h-8 w-[60px]" />
          </CardContent>
        </Card>
      ))}
    </>
  );
}
