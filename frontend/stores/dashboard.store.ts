import { create } from 'zustand';
import { OverviewData } from '@/services/Types/dashboard-types';

type DashboardStore = {
  overviewData: OverviewData | null;
  setOverviewData: (data: OverviewData) => void;
  clearOverviewData: () => void;
  daysFilter: number;
  setDaysFilter: (days: number) => void;
};

export const useDashboardStore = create<DashboardStore>((set) => ({
  overviewData: null,
  setOverviewData: (data) => set({ overviewData: data }),
  clearOverviewData: () => set({ overviewData: null, daysFilter: 7 }),
  daysFilter: 7,
  setDaysFilter: (days) => set({ daysFilter: days }),
}));
