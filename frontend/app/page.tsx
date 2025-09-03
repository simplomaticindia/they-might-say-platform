'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect based on authentication status
    if (isAuthenticated()) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  // Show loading state while redirecting
  return (
    <div className="min-h-screen bg-gradient-to-br from-historical-50 via-lincoln-50 to-historical-100 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-lincoln-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <h1 className="text-2xl font-bold text-gray-900 font-historical">They Might Say</h1>
        <p className="text-gray-600 mt-2">Loading...</p>
      </div>
    </div>
  );
}