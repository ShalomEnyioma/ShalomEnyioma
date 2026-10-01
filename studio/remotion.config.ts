import { Config } from '@remotion/cli/config';

// Use the Chromium that is pre-installed in the cloud environment
// (set REMOTION_BROWSER to override on another machine).
Config.setBrowserExecutable(
  process.env.REMOTION_BROWSER ??
    '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
);
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
