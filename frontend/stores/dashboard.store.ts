import { create } from 'zustand';
import { OverviewData } from '@/services/Types/dashboard-types';

type DashboardStore = {
  overviewData: OverviewData | null;
  setOverviewData: (data: OverviewData) => void;
  daysFilter: number;
  setDaysFilter: (days: number) => void;
};

export const useDashboardStore = create<DashboardStore>((set) => ({
  overviewData: null,
  setOverviewData: (data) => set({ overviewData: data }),
  daysFilter: 7,
  setDaysFilter: (days) => set({ daysFilter: days }),
}));
