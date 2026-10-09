#!/usr/bin/env python3
"""Доля пересвеченных пикселей (любой канал ≥ 250) в PNG: clipcheck.py a.png b.png …
> 0.5 % на главном объекте — засвет; правка яркости/Specular, а не «нормально»."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import c4dlib as L
for p in sys.argv[1:]:
    c = L.clip_pct(p)
    print("%s %.2f%%%s" % (os.path.basename(p), c, "  WARN" if c > 0.5 else ""))
