import '@fontsource/inter/500.css';
import '@fontsource/inter/700.css';
import '@fontsource/inter/800.css';
import '@fontsource/inter/900.css';
import React from 'react';
import { Composition } from 'remotion';
import { ShallyShort } from './ShallyShort';
import { CANVAS } from './brand';
import type { VideoSpec } from './types';
import example from '../specs/example.json';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="ShallyShort"
    component={ShallyShort}
    fps={FPS}
    width={CANVAS.width}
    height={CANVAS.height}
    durationInFrames={FPS * 10}
    defaultProps={example as VideoSpec}
    calculateMetadata={({ props }) => ({
      durationInFrames: Math.ceil(props.durationSec * FPS),
    })}
  />
);
