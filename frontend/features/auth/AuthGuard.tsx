'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/auth';
import { removeTokens } from '@/utils/auth-utils';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function verifySession() {
      const accessToken = localStorage.getItem('accessToken');
      const refreshToken = localStorage.getItem('refreshToken');

      if (accessToken) {
        setIsReady(true);
        return;
      }

      if (!refreshToken) {
        removeTokens();
        router.replace('/');
        return;
      }

      try {
        await authService.RefreshTokens();
        if (isMounted) {
          setIsReady(true);
        }
      } catch {
        removeTokens();
        router.replace('/');
      }
    }

    verifySession();

    return () => {
      isMounted = false;
    };
  }, [router]);

  if (!isReady) {
    return null;
  }

  return children;
}
