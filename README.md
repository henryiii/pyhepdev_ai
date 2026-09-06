# PyHEP.dev 2026 - September

To get started, install marimo:

```bash
uv tool install marimo[recommended]
```

Then `marimo edit`. Or install the skill in an AI agent:

```
gh skill marimo-team/marimo-pair
```

And run `/marimo-pair pair with me on ai_sept_2026.py` in a harness.

To make slides:

```bash
uv tool install marimo[recommended] --with nbconvert --with playwright
uv tool install playwright
playwright install chromium
marimo export pdf ai_sept_2026.py -o ai_sept_2026.pdf --as=slides --raster-server=live
```

However, they look terrible: skipped slides are not skipped.

