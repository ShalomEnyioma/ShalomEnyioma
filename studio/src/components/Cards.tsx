import React from 'react';
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRAND, CARD_AREA } from '../brand';
import type { Card } from '../types';

const resolve = (src: string) => (/^https?:\/\//.test(src) ? src : staticFile(src));

const cardBase: React.CSSProperties = {
  background: BRAND.white,
  borderRadius: 36,
  border: `2px solid ${BRAND.cardBorder}`,
  boxShadow: '0 24px 60px rgba(0,0,0,0.10)',
  fontFamily: BRAND.font,
  color: BRAND.ink,
};

// Pop-in with a slow float so cards never sit dead still.
const useEntrance = (delay: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 13, stiffness: 140 } });
  const float = Math.sin((frame - delay) / 22) * 6;
  return {
    opacity: interpolate(s, [0, 1], [0, 1]),
    transform: `translateY(${interpolate(s, [0, 1], [70, 0]) + float}px) scale(${interpolate(s, [0, 1], [0.9, 1])})`,
  };
};

const Staggered: React.FC<{ i: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  i,
  children,
  style,
}) => {
  const anim = useEntrance(6 + i * 7);
  return <div style={{ ...style, ...anim }}>{children}</div>;
};

const ListCard: React.FC<{ items: { icon?: string; label: string }[] }> = ({ items }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 22, width: 900 }}>
    {items.map((it, i) => (
      <Staggered key={i} i={i} style={{ ...cardBase, display: 'flex', alignItems: 'center', gap: 28, padding: '26px 34px' }}>
        <div
          style={{
            width: 74,
            height: 74,
            borderRadius: 22,
            background: BRAND.red,
            color: BRAND.white,
            fontSize: it.icon ? 40 : 38,
            fontWeight: 900,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          {it.icon ?? i + 1}
        </div>
        <div style={{ fontSize: 44, fontWeight: 800 }}>{it.label}</div>
      </Staggered>
    ))}
  </div>
);

const StepsCard: React.FC<{ items: string[] }> = ({ items }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 860 }}>
    {items.map((label, i) => (
      <React.Fragment key={i}>
        <Staggered i={i} style={{ ...cardBase, width: '100%', padding: '28px 36px', display: 'flex', gap: 24, alignItems: 'center' }}>
          <div style={{ fontSize: 40, fontWeight: 900, color: BRAND.red, width: 56 }}>{String(i + 1).padStart(2, '0')}</div>
          <div style={{ fontSize: 44, fontWeight: 800 }}>{label}</div>
        </Staggered>
        {i < items.length - 1 && (
          <Staggered i={i + 0.5} style={{ width: 6, height: 40, background: `repeating-linear-gradient(${BRAND.red} 0 8px, transparent 8px 16px)` }}>
            {null}
          </Staggered>
        )}
      </React.Fragment>
    ))}
  </div>
);

const StatCard: React.FC<{ value: string; label: string }> = ({ value, label }) => (
  <Staggered i={0} style={{ ...cardBase, padding: '50px 70px', textAlign: 'center', minWidth: 640 }}>
    <div style={{ fontSize: 170, fontWeight: 900, color: BRAND.red, lineHeight: 1 }}>{value}</div>
    <div style={{ fontSize: 46, fontWeight: 700, marginTop: 18 }}>{label}</div>
  </Staggered>
);

const ImageCard: React.FC<{ src: string; caption?: string }> = ({ src, caption }) => (
  <Staggered i={0} style={{ ...cardBase, padding: 18, width: 760 }}>
    <Img src={resolve(src)} style={{ width: '100%', height: 560, objectFit: 'cover', borderRadius: 24, display: 'block' }} />
    {caption && <div style={{ fontSize: 38, fontWeight: 800, padding: '20px 10px 6px', textAlign: 'center' }}>{caption}</div>}
  </Staggered>
);

const TagsCard: React.FC<{ title?: string; tags: string[] }> = ({ title, tags }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 34, width: 920 }}>
    {title && (
      <Staggered i={0} style={{ ...cardBase, padding: '30px 44px', fontSize: 50, fontWeight: 900, textAlign: 'center' }}>
        {title}
      </Staggered>
    )}
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, justifyContent: 'center' }}>
      {tags.map((t, i) => (
        <Staggered
          key={i}
          i={i + 1}
          style={{
            background: i % 2 === 0 ? BRAND.red : BRAND.ink,
            color: BRAND.white,
            fontFamily: BRAND.font,
            fontWeight: 800,
            fontSize: 40,
            padding: '18px 34px',
            borderRadius: 999,
          }}
        >
          {t}
        </Staggered>
      ))}
    </div>
  </div>
);

const CompareCard: React.FC<Extract<Card, { type: 'compare' }>> = ({ left, right }) => (
  <div style={{ display: 'flex', gap: 26, width: 960 }}>
    {[left, right].map((side, i) => (
      <Staggered key={i} i={i * 2} style={{ ...cardBase, flex: 1, padding: '34px 30px', borderTop: `14px solid ${i === 0 ? '#BDBDBD' : BRAND.red}` }}>
        <div style={{ fontSize: 42, fontWeight: 900, color: i === 0 ? BRAND.muted : BRAND.red, marginBottom: 20 }}>{side.title}</div>
        {side.lines.map((l, j) => (
          <div key={j} style={{ fontSize: 36, fontWeight: 700, margin: '12px 0', textDecoration: i === 0 ? 'line-through' : 'none', color: i === 0 ? BRAND.muted : BRAND.ink }}>
            {i === 0 ? '✕ ' : '✓ '}
            {l}
          </div>
        ))}
      </Staggered>
    ))}
  </div>
);

const TextCard: React.FC<{ title: string; body?: string }> = ({ title, body }) => (
  <Staggered i={0} style={{ ...cardBase, padding: '46px 54px', width: 880, borderLeft: `16px solid ${BRAND.red}` }}>
    <div style={{ fontSize: 60, fontWeight: 900, lineHeight: 1.15 }}>{title}</div>
    {body && <div style={{ fontSize: 40, fontWeight: 600, color: BRAND.muted, marginTop: 20, lineHeight: 1.3 }}>{body}</div>}
  </Staggered>
);

const CtaCard: React.FC<{ text: string; sub?: string }> = ({ text, sub }) => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin(frame / 6) * 0.03;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30 }}>
      <Staggered i={0} style={{ ...cardBase, padding: '36px 48px', display: 'flex', alignItems: 'center', gap: 28 }}>
        <div style={{ width: 120, height: 120, borderRadius: 60, background: BRAND.red, color: BRAND.white, fontSize: 64, fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          S
        </div>
        <div>
          <div style={{ fontSize: 48, fontWeight: 900 }}>{BRAND.handle}</div>
          <div style={{ fontSize: 34, fontWeight: 600, color: BRAND.muted }}>{sub ?? 'Helping YOU leverage AI'}</div>
        </div>
      </Staggered>
      <Staggered i={2} style={{ transform: `scale(${pulse})` }}>
        <div style={{ background: BRAND.red, color: BRAND.white, fontFamily: BRAND.font, fontWeight: 900, fontSize: 54, padding: '28px 60px', borderRadius: 999, boxShadow: '0 18px 40px rgba(225,29,46,0.4)' }}>
          {text}
        </div>
      </Staggered>
    </div>
  );
};

const renderCard = (card: Card) => {
  switch (card.type) {
    case 'list':
      return <ListCard items={card.items} />;
    case 'steps':
      return <StepsCard items={card.items} />;
    case 'stat':
      return <StatCard value={card.value} label={card.label} />;
    case 'image':
      return <ImageCard src={card.src} caption={card.caption} />;
    case 'tags':
      return <TagsCard title={card.title} tags={card.tags} />;
    case 'compare':
      return <CompareCard {...card} />;
    case 'text':
      return <TextCard title={card.title} body={card.body} />;
    case 'cta':
      return <CtaCard text={card.text} sub={card.sub} />;
  }
};

export const CardArea: React.FC<{ cards: Card[] }> = ({ cards }) => (
  <div
    style={{
      position: 'absolute',
      top: CARD_AREA.top,
      height: CARD_AREA.bottom - CARD_AREA.top,
      left: 0,
      right: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 30,
    }}
  >
    {cards.map((c, i) => (
      <React.Fragment key={i}>{renderCard(c)}</React.Fragment>
    ))}
  </div>
);
