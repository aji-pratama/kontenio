/**
 * Remotion Configuration for AI Video Factory
 * 
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

// Video output settings
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// Codec settings for high-quality output
Config.setCodec("h264");
Config.setCrf(18); // Quality level (lower = better, 18 is visually lossless)

// Public directory contains symlink to backend/media
Config.setPublicDir("./public");

// Enable Tailwind for styling
Config.overrideWebpackConfig(enableTailwind);
