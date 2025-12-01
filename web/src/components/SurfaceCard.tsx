import type { ReactNode } from 'react';

type ElementTag = keyof JSX.IntrinsicElements;

type SurfaceCardProps<T extends ElementTag = 'div'> = {
  as?: T;
  className?: string;
  children: ReactNode;
} & Omit<JSX.IntrinsicElements[T], 'className'>;

const BASE_CLASS = 'rounded-xl shadow';

export function SurfaceCard<T extends ElementTag = 'div'>({ as, className = '', children, ...rest }: SurfaceCardProps<T>) {
  const Component = (as ?? 'div') as ElementTag;
  const classes = [BASE_CLASS, className].filter(Boolean).join(' ').trim();
  return (
    <Component className={classes} {...rest}>
      {children}
    </Component>
  );
}

export default SurfaceCard;
