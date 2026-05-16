# Brand assets

Visual identity for the Liminate Programming Language. The full identity reference (system, scale, in-context surfaces) lives in `liminate_visual_identity.html` at the project root during build sessions; the files here are the extracted production assets.

## Files

| File | When to use |
|---|---|
| `mark-amber.svg` | The Amber mark alone. App icons, social avatars, small-context branding, favicons. |
| `mark-reversed.svg` | The reversed mark for use on amber backgrounds. White rectangle, amber lines. |
| `wordmark-primary-light.svg` | Primary Threshold wordmark on light backgrounds. Display sizes, marketing, documentation headers. Mixed typeface: Alegreya italic 500 (`in`) + Red Hat Mono 400 (`script`). Ink text. |
| `wordmark-primary-dark.svg` | Same primary wordmark on dark backgrounds. Bone text. |
| `wordmark-compact-light.svg` | Compact lockup on light backgrounds. Alegreya regular 400 for the full word (no italic, no mono split). Use where the mixed typeface can't reproduce cleanly — small UI, monochrome print, contexts at very small scale. |
| `wordmark-compact-dark.svg` | Compact lockup on dark backgrounds. Bone text. |

## Color rules

- The mark is invariant. It is always amber (`#C0780F`) on light/dark, or white on an amber background (the reversed variant). Do not recolor the mark.
- Only the wordmark text color adapts: Ink (`#0B1C38`) on light, Bone (`#E8DFD0`) on dark.

## Clear space

- Around the lockup: minimum clear space on all sides equals the height of the mark.
- Around the standalone mark: minimum clear space equals half the mark height.

## Palette

| Token | Hex |
|---|---|
| Amber | `#C0780F` |
| Ink | `#0B1C38` |
| Bone | `#E8DFD0` |
| Paper | `#F5F1E8` |
| Night | `#111018` |

## Typography

| Role | Face | Use for |
|---|---|---|
| Editorial | Alegreya | Headings, quotes, narrative |
| Code | Red Hat Mono | Source, CLI, technical |
| Interface | Figtree | UI, labels, navigation |

The wordmark SVGs reference these font families with system-font fallbacks (`Georgia`, `monospace`). Google Fonts cannot be loaded inside an SVG `<image>` context — when embedding the wordmark in environments where Alegreya and Red Hat Mono are not installed, prefer rasterising the SVG to PNG at the target size, or load the fonts in the surrounding page.
