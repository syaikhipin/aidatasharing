'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SimplifiedConnectionsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the unified sharing hub with the connectors tab active
    router.replace('/datasets/sharing?tab=connectors');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}