import { getProduct, type ProductId } from '@/features/product/products';

type LaSuiteLogoProps = {
  className?: string;
  product?: ProductId | string | null;
};

const DEFAULT_LOGO = {
  src: '/assets/lasuite-logomark.svg',
  width: 130,
  height: 40,
} as const;

export const LaSuiteLogo = ({
  className = '',
  product: productId,
}: LaSuiteLogoProps) => {
  const product = getProduct(productId);
  const isDefault = !product;

  return (
    <span
      className={`app-logo${isDefault ? ' app-logo--default' : ''} ${className}`.trim()}
      role="img"
      aria-label={product?.label ?? 'La Suite'}
    >
      <img
        className="app-logo__image"
        src={product?.logo ?? DEFAULT_LOGO.src}
        alt=""
        width={isDefault ? DEFAULT_LOGO.width : undefined}
        height={isDefault ? DEFAULT_LOGO.height : 40}
      />
    </span>
  );
};
