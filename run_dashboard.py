"""
Bank Nifty F&O Decision Support System
Streamlit Dashboard Entry Point.

Run with: streamlit run run_dashboard.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run dashboard
from dashboard.app import main

if __name__ == "__main__":
    main()
