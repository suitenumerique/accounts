import { useRouter } from 'next/router';

import { getProduct, isProductId, type ProductId } from './products';

const getQueryValue = (value: string | string[] | undefined) => {
  if (Array.isArray(value)) {
    return value.at(-1);
  }

  return value;
};

export const useProduct = (product?: ProductId | string | null) => {
  const router = useRouter();
  const queryProduct = getQueryValue(router.query.product);

  const productId =
    (product && isProductId(product) && product) ||
    (queryProduct && isProductId(queryProduct) && queryProduct) ||
    undefined;

  return {
    productId,
    product: getProduct(productId),
  };
};
