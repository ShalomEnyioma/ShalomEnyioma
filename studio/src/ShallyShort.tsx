import React from 'react';
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRAND, CANVAS, PRESENTER_FRAME } from './brand';
import { CardArea } from './components/Cards';
import { Captions } from './components/Captions';
import { Presenter } from './components/Presenter';
import { GridBackground, HandleTag, HeaderPill, ProgressBar } from './components/Stage';
import type { Scene, VideoSpec } from './types';

const TRANSITION = 7; // frames to morph between full-frame and bottom-third

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

export const ShallyShort: React.FC<VideoSpec> = (spec) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  const scenes = spec.scenes;
  const idx = Math.max(0, scenes.findIndex((s) => t >= s.start && t < s.end));
  const scene: Scene = scenes[idx] ?? scenes[scenes.length - 1];
  const prev = scenes[idx - 1];

  // 1 = presenter in bottom frame (stage), 0 = full frame (a-roll).
  const target = scene.mode === 'stage' ? 1 : 0;
  const from = prev ? (prev.mode === 'stage' ? 1 : 0) : target;
  const sinceStart = frame - Math.round(scene.start * fps);
  const p = interpolate(sinceStart, [0, TRANSITION], [from, target], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const box = {
    x: lerp(0, PRESENTER_FRAME.x, p),
    y: lerp(0, PRESENTER_FRAME.y, p),
    w: lerp(CANVAS.width, PRESENTER_FRAME.width, p),
    h: lerp(CANVAS.height, PRESENTER_FRAME.height, p),
    r: lerp(0, PRESENTER_FRAME.radius, p),
  };

  // Punch-in on a-roll lines marked punchIn.
  const sceneLen = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const zoom =
    scene.mode === 'aroll' && scene.punchIn
      ? interpolate(sinceStart, [0, 5, sceneLen], [1, 1.12, 1.16], { extrapolateRight: 'clamp' })
      : 1;

  const footageStart = Math.round((spec.footageStartSec ?? 0) * fps);
  const onStage = p > 0.5;
  const captionBottom = onStage ? CANVAS.height - PRESENTER_FRAME.y + 40 : 470;

  return (
    <AbsoluteFill style={{ backgroundColor: BRAND.stageBg }}>
      {p > 0 && <GridBackground />}

      {/* Presenter (single continuous video so audio never cuts) */}
      <div
        style={{
          position: 'absolute',
          left: box.x,
          top: box.y,
          width: box.w,
          height: box.h,
          borderRadius: box.r,
          overflow: 'hidden',
          border: p > 0.5 ? `6px solid ${BRAND.red}` : 'none',
          boxShadow: p > 0.5 ? '0 30px 70px rgba(0,0,0,0.25)' : 'none',
        }}
      >
        <Presenter footage={spec.footage} startFrom={footageStart} zoom={zoom} />
      </div>

      {/* Scene overlays */}
      {scenes.map((s, i) => (
        <Sequence key={i} from={Math.round(s.start * fps)} durationInFrames={Math.max(1, Math.round((s.end - s.start) * fps))}>
          {s.header && <HeaderPill text={s.header} number={s.number} />}
          {s.mode === 'stage' && s.cards && s.cards.length > 0 && <CardArea cards={s.cards} />}
          {s.sfx && <Audio src={staticFile(`sfx/${s.sfx}.wav`)} volume={0.55} />}
        </Sequence>
      ))}

      <Captions words={spec.captions} bottom={captionBottom} onLight={onStage} />
      <HandleTag onDark={p < 0.5} />
      <ProgressBar progress={frame / durationInFrames} />

      {spec.music && <Audio src={staticFile(spec.music)} volume={spec.musicVolume ?? 0.12} loop />}
    </AbsoluteFill>
  );
};
