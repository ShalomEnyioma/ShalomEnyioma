import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRAND } from '../brand';
import type { Caption } from '../types';

// Group words into short lines (max 3 words, break on punctuation or pauses).
const groupWords = (words: Caption[]) => {
  const groups: Caption[][] = [];
  let cur: Caption[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const next = words[i + 1];
    const pause = next ? next.start - w.end > 0.35 : true;
    if (cur.length >= 3 || /[.,!?;:]$/.test(w.text) || pause) {
      groups.push(cur);
      cur = [];
    }
  });
  if (cur.length) groups.push(cur);
  return groups;
};

// Word-by-word captions. The active word sits in a red pill.
// `bottom` anchors the block so long lines wrap upwards, never into the presenter frame.
export const Captions: React.FC<{ words: Caption[]; bottom: number; onLight: boolean }> = ({
  words,
  bottom,
  onLight,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const groups = React.useMemo(() => groupWords(words), [words]);
  const group = groups.find((g) => t >= g[0].start && t < g[g.length - 1].end + 0.15);
  if (!group) return null;
  const pop = interpolate(t - group[0].start, [0, 0.12], [0.85, 1], { extrapolateRight: 'clamp' });

  return (
    <div
      style={{
        position: 'absolute',
        bottom,
        left: 40,
        right: 40,
        display: 'flex',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: 14,
        transform: `scale(${pop})`,
      }}
    >
      {group.map((w, i) => {
        const active = t >= w.start && t < w.end + 0.05;
        return (
          <span
            key={i}
            style={{
              fontFamily: BRAND.font,
              fontWeight: 900,
              fontSize: onLight ? 66 : 76,
              lineHeight: 1.15,
              textTransform: 'uppercase',
              color: active || !onLight ? BRAND.white : BRAND.ink,
              padding: '4px 18px',
              borderRadius: 18,
              background: active ? BRAND.red : 'transparent',
              textShadow: active || onLight ? 'none' : '0 4px 16px rgba(0,0,0,0.7), 0 0 3px rgba(0,0,0,0.9)',
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
