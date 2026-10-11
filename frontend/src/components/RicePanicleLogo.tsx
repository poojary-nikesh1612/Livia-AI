// src/components/RicePanicleLogo.tsx
import React from 'react';
import { Image, StyleSheet } from 'react-native';

interface RicePanicleLogoProps {
  /** Width and height of the logo in px (default 34) */
  size?: number;
}

const ICON_SOURCE = require('../../assets/icon.png');

/**
 * Displays the Livia AI logo image from `frontend/assets/icon.png`
 * with proper sizing and aspect-ratio preservation.
 */
export const RicePanicleLogo: React.FC<RicePanicleLogoProps> = ({ size = 34 }) => {
  return (
    <Image
      source={ICON_SOURCE}
      style={[styles.logoImage, { width: size, height: size }]}
      resizeMode="contain"
      accessibilityIgnoresInvertColors
    />
  );
};

const styles = StyleSheet.create({
  logoImage: {
    width: 34,
    height: 34,
  },
});
