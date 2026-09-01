import { create } from 'zustand';

export const useAuthCard = create((set) => ({
  tab: 1,
  setActiveTab: (activeTab: number) => set({ tab: activeTab }),
}));
