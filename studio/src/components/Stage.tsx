import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRAND } from '../brand';

// White grid "stage" that sits behind cards in stage mode.
export const GridBackground: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundColor: BRAND.stageBg,
      backgroundImage: `linear-gradient(${BRAND.gridLine} 2px, transparent 2px), linear-gradient(90deg, ${BRAND.gridLine} 2px, transparent 2px)`,
      backgroundSize: '72px 72px',
    }}
  />
);

// Red header pill at the top of the frame, with an optional number badge.
export const HeaderPill: React.FC<{ text: string; number?: number; dark?: boolean }> = ({ text, number }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 14, stiffness: 160 } });
  return (
    <div
      style={{
        position: 'absolute',
        top: 130,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        transform: `translateY(${interpolate(s, [0, 1], [-60, 0])}px) scale(${interpolate(s, [0, 1], [0.85, 1])})`,
        opacity: s,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 22,
          background: BRAND.red,
          color: BRAND.white,
          fontFamily: BRAND.font,
          fontWeight: 900,
          fontSize: 50,
          lineHeight: 1.1,
          padding: number !== undefined ? '18px 40px 18px 18px' : '22px 44px',
          borderRadius: 999,
          maxWidth: 960,
          textAlign: 'center',
          boxShadow: '0 14px 36px rgba(225,29,46,0.35)',
        }}
      >
        {number !== undefined && (
          <div
            style={{
              flexShrink: 0,
              width: 76,
              height: 76,
              borderRadius: 38,
              background: BRAND.white,
              color: BRAND.red,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 46,
            }}
          >
            {number}
          </div>
        )}
        <span>{text}</span>
      </div>
    </div>
  );
};

// Thin progress bar across the very top: a small retention cue.
export const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
  <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 12, background: 'rgba(0,0,0,0.08)' }}>
    <div style={{ width: `${progress * 100}%`, height: '100%', background: BRAND.red }} />
  </div>
);

export const HandleTag: React.FC<{ onDark: boolean }> = ({ onDark }) => (
  <div
    style={{
      position: 'absolute',
      top: 44,
      left: 50,
      fontFamily: BRAND.font,
      fontWeight: 800,
      fontSize: 30,
      color: onDark ? BRAND.white : BRAND.ink,
      opacity: 0.85,
      textShadow: onDark ? '0 2px 8px rgba(0,0,0,0.6)' : 'none',
    }}
  >
    <span style={{ color: BRAND.red }}>●</span> {BRAND.handle}
  </div>
);
