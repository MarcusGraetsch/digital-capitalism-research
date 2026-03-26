#!/usr/bin/env python3
"""Wrapper to run fetch_metrics with proper imports."""

import sys
import os

# Add literature_pipeline to path
sys.path.insert(0, '/root/.openclaw/workspace/literature_pipeline')

# Change to correct directory
os.chdir('/root/.openclaw/workspace/literature_pipeline')

# Now import and run
from fetch_metrics import main

if __name__ == "__main__":
    main()
