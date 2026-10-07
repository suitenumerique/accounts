export const PRODUCTS = {
  assistant: {
    label: 'Assistant',
    logo: '/images/assistant.svg',
  },
  docs: {
    label: 'Docs',
    logo: '/images/docs.svg',
  },
  fichiers: {
    label: 'Fichiers',
    logo: '/images/fichiers.svg',
  },
  grist: {
    label: 'Grist',
    logo: '/images/grist.svg',
  },
  messagerie: {
    label: 'Messagerie',
    logo: '/images/messagerie.svg',
  },
  regie: {
    label: 'Régie',
    logo: '/images/regie.svg',
  },
  tchap: {
    label: 'Tchap',
    logo: '/images/tchap.svg',
  },
  transcripts: {
    label: 'Transcripts',
    logo: '/images/transcripts.svg',
  },
  visio: {
    label: 'Visio',
    logo: '/images/visio.svg',
  },
} as const;

export type ProductId = keyof typeof PRODUCTS;

export const isProductId = (value: string): value is ProductId =>
  value in PRODUCTS;

export const getProduct = (productId?: string | null) => {
  if (!productId || !isProductId(productId)) {
    return undefined;
  }

  return PRODUCTS[productId];
};
