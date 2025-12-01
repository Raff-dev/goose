import * as React from 'react';

import SurfaceCard from './SurfaceCard';

interface SummaryMetricCardProps {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  status?: 'default' | 'success' | 'danger';
}

export function SummaryMetricCard({ label, value, icon, status = 'default' }: SummaryMetricCardProps) {
  const iconBgColor =
    status === 'success' ? 'bg-green-100' :
    status === 'danger' ? 'bg-red-100' :
    'bg-blue-100';
  const iconTextColor =
    status === 'success' ? 'text-green-600' :
    status === 'danger' ? 'text-red-800' :
    'text-blue-600';

  return (
    <SurfaceCard className="flex flex-col items-start justify-between bg-white px-6 py-4 min-w-[160px] min-h-[100px]">
      <span className="text-xs text-gray-500 font-medium mb-2">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-3xl font-bold tracking-tight">{value}</span>
        {icon && (
          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${iconBgColor} ${iconTextColor}`}>
            {icon}
          </span>
        )}
      </div>
    </SurfaceCard>
  );
}
