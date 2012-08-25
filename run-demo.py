#!/usr/bin/env python

from rawkitlawnchair.launchers import DreamCheeky_StormOIC
from rawkitlawnchair.kernels import PanTracker

k = PanTracker(DreamCheeky_StormOIC())

k.run()
