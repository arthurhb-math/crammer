#!/usr/bin/env python3
"""
Crammer - Academic Assessment Generation System

Main entry point for the GUI application.
Run this file to start Crammer.
"""

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crammer.gui.app import main

if __name__ == "__main__":
    main()
