type LaSuiteLogoProps = {
  variant?: 'wordmark' | 'mark';
  className?: string;
};

export const LaSuiteLogo = ({
  variant = 'wordmark',
  className,
}: LaSuiteLogoProps) => {
  const isMark = variant === 'mark';

  return (
    <span
      className={['app-logo', `app-logo--${variant}`, className]
        .filter(Boolean)
        .join(' ')}
      role="img"
      aria-label="La Suite"
    >
      <img
        className="app-logo__image"
        src={isMark ? '/assets/lasuite-mark.svg' : '/assets/lasuite-logomark.svg'}
        alt=""
        width={isMark ? 32 : 130}
        height={isMark ? 32 : 40}
      />
    </span>
  );
};
