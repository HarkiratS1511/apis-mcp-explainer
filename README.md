# Plugging AI into your other apps

An interactive explainer of APIs and MCP, made for a live teaching session. Part 1 (APIs) is presented by Ritesh, Part 2 (MCP) by Harkirat.

A teaching demo, not an official Dragonfly Thinking product.

## Presenting

Open the page in a browser at full screen (F11). Use the arrow keys or Page Up / Page Down to move between sections.

## Editing

Each section is its own file in `src/sections/`. After changing one, rebuild:

```
python3 -I src/build.py
```

This writes `dist/index.html` and checks the sections for common mistakes.

To publish the new version:

```
git subtree push --prefix dist origin gh-pages
```
