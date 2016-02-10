#!/usr/bin/env python

import os
from glob import glob

dirs = [fn for fn in glob('./*') if os.path.isdir(fn)]
print(len(dirs), dirs)
