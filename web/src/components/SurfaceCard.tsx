import type { ComponentPropsWithoutRef, ElementType, ReactNode } from 'react';

type SurfaceCardProps<T extends ElementType = 'div'> = {
  as?: T;
  className?: string;
  children?: ReactNode;
} & Omit<ComponentPropsWithoutRef<T>, 'as' | 'className' | 'children'>;

const BASE_CLASS = 'rounded-xl shadow';

export function SurfaceCard<T extends ElementType = 'div'>({ as, className = '', children, ...rest }: SurfaceCardProps<T>) {
  const Component = (as ?? 'div') as ElementType;
  const classes = [BASE_CLASS, className].filter(Boolean).join(' ').trim();
  return (
    <Component className={classes} {...rest}>
      {children}
    </Component>
  );
}

export default SurfaceCard;
