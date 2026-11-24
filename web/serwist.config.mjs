// Service worker build (Serwist + Turbopack): runs after `next build`.
import { serwist } from "@serwist/next/config";

export default serwist({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  // Never precache documents or anything behind /files: they hold personal data.
  globIgnores: ["**/files/**"],
});
