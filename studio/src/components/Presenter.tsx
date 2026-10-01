import React from 'react';
import { AbsoluteFill, OffthreadVideo, staticFile } from 'remotion';
import { BRAND } from '../brand';

const resolve = (src: string) => (/^https?:\/\//.test(src) ? src : staticFile(src));

// The talking-head footage, or a placeholder when no footage is set yet.
export const Presenter: React.FC<{ footage?: string; startFrom: number; zoom: number }> = ({
  footage,
  startFrom,
  zoom,
}) => {
  if (!footage) {
    return (
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 35%, #3a3a3a 0%, #151515 70%)`,
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${zoom})`,
        }}
      >
        <div style={{ width: 300, height: 300, borderRadius: 150, background: '#2b2b2b', marginTop: -200 }} />
        <div style={{ width: 560, height: 420, borderRadius: '280px 280px 0 0', background: '#2b2b2b', marginTop: 30 }} />
        <div
          style={{
            position: 'absolute',
            bottom: 60,
            fontFamily: BRAND.font,
            fontWeight: 700,
            fontSize: 34,
            letterSpacing: 4,
            color: '#8a8a8a',
          }}
        >
          YOUR FOOTAGE HERE
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
      <OffthreadVideo
        src={resolve(footage)}
        startFrom={startFrom}
        style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 30%' }}
      />
    </AbsoluteFill>
  );
};
