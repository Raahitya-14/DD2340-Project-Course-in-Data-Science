#!/usr/bin/env python3
"""Launch Sionna AI Agent Chat Interface"""
import sys
import os
from pathlib import Path

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.ui.chat import ChatInterface

if __name__ == "__main__":
    interface = ChatInterface()
    interface.launch(share=False)
