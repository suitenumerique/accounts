import { Box, BoxType } from '../Box';

export const HorizontalSeparator = (props: BoxType) => {
  return (
    <Box
      $height="1px"
      $width="100%"
      $margin={{ vertical: 'base' }}
      $background="var(--c--contextuals--border--surface--primary)"
      className="--accounts--horizontal-separator"
      {...props}
    />
  );
};
