#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VietTraffic - Unified Paced Crawler Launcher (CCTV & Google Maps)
Author: Master Bach Khoa Student Project
"""

import sys
import os

# Append project root to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawlers import unified_crawler

if __name__ == "__main__":
    try:
        unified_crawler.main()
    except KeyboardInterrupt:
        print("\n[!] Crawler terminated by user.")
        sys.exit(0)
