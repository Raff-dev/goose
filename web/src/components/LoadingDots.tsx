interface LoadingDotsProps {
  className?: string;
  dotClassName?: string;
}

const DOT_DELAYS = ['0ms', '150ms', '300ms'];

export default function LoadingDots({ className = '', dotClassName = '' }: LoadingDotsProps) {
  return (
    <span className={`flex items-center gap-1 ${className}`} aria-hidden="true">
      {DOT_DELAYS.map((delay) => (
        <span
          key={delay}
          className={`h-1.5 w-1.5 rounded-full bg-white opacity-90 animate-bounce ${dotClassName}`.trim()}
          style={{ animationDelay: delay }}
        />
      ))}
    </span>
  );
}
