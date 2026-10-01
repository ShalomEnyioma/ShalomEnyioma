// A video is described by one JSON "spec" file (see specs/*.json).
// All times are in seconds from the start of the video.

export type Caption = { text: string; start: number; end: number };

export type Card =
  | { type: 'list'; items: { icon?: string; label: string }[] }
  | { type: 'steps'; items: string[] }
  | { type: 'stat'; value: string; label: string }
  | { type: 'image'; src: string; caption?: string }
  | { type: 'tags'; title?: string; tags: string[] }
  | { type: 'compare'; left: { title: string; lines: string[] }; right: { title: string; lines: string[] } }
  | { type: 'text'; title: string; body?: string }
  | { type: 'cta'; text: string; sub?: string };

export type Sfx = 'whoosh' | 'pop' | 'click' | 'riser' | 'hit' | 'ding';

export type Scene = {
  start: number;
  end: number;
  mode: 'stage' | 'aroll';
  header?: string;
  number?: number;
  cards?: Card[];
  punchIn?: boolean;
  sfx?: Sfx;
};

export type VideoSpec = {
  title?: string;
  durationSec: number;
  footage?: string; // file in studio/public (e.g. "footage/take1.mp4") or https URL
  footageStartSec?: number;
  captions: Caption[];
  scenes: Scene[];
  music?: string; // file in studio/public
  musicVolume?: number;
};
