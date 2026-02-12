# Convai Plugin Content

This repository contains dynamic content feeds for Convai plugins across different platforms.

## What is this?

This repository hosts announcement feeds and changelog information that is automatically displayed in Convai plugins. When you open the Convai plugin in your game engine (Unreal Engine, Unity, etc.), you'll see the latest updates, features, and news - all pulled from this repository.

## Content Files

- **announcements-common.json** - General announcements for all platforms
- **announcements-unreal.json** - Unreal Engine specific announcements
- **changelogs-common.json** - Core platform updates
- **changelogs-unreal.json** - Unreal Engine plugin release notes

Additional platform files will be added as Convai expands to more game engines.

## How it works

1. Content is updated in this repository
2. Files are automatically distributed
3. Plugin users see the updates in their editor within minutes

## Quality Gates

This repository includes CI checks for production safety:

- **Schema Validation** on PR/push for all feed JSON files
- **Canary Monitoring** on `main` pushes to compare `raw.githubusercontent.com` vs `jsDelivr`

If canary detects CDN divergence, CI emits warnings and opens/updates an issue labeled `content-canary`.

## License

MIT License

---

**Maintained by the Convai Team**  
