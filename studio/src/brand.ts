// ShallyBuilds brand tokens. Red + white, with near-black ink for text.
export const BRAND = {
  handle: '@shallybuilds',
  red: '#E11D2E',
  redDark: '#B3121F',
  white: '#FFFFFF',
  ink: '#0A0A0A',
  muted: '#6B6B6B',
  stageBg: '#FAFAFA',
  gridLine: '#ECECEC',
  cardBorder: '#EFEFEF',
  font: "'Inter', system-ui, sans-serif",
} as const;

export const CANVAS = { width: 1080, height: 1920 } as const;

// Presenter frame used in "stage" mode (bottom third).
export const PRESENTER_FRAME = { x: 70, y: 1180, width: 940, height: 660, radius: 44 } as const;

// Area where floating cards live in "stage" mode.
export const CARD_AREA = { top: 300, bottom: 1040 } as const;
