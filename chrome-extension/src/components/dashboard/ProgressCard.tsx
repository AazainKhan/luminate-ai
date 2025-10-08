/**
 * ProgressCard Component
 * Reusable metric card for dashboard
 */

import { LucideIcon } from 'lucide-react';
import { Card } from '../ui/card';
import { cn } from '@/lib/utils';

interface ProgressCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color: string;
  bgColor: string;
  subtitle?: string;
  onClick?: () => void;
}

export function ProgressCard({
  icon: Icon,
  label,
  value,
  color,
  bgColor,
  subtitle,
  onClick,
}: ProgressCardProps) {
  return (
    <Card
      className={cn(
        'p-4 transition-all',
        onClick && 'cursor-pointer hover:shadow-lg hover:scale-[1.02]'
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className={cn('p-2 rounded-lg', bgColor)}>
          <Icon className={cn('h-5 w-5', color)} />
        </div>
        <div className="flex-1">
          <p className="text-xs text-muted-foreground mb-1">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </Card>
  );
}

