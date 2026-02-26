"""Wrapper to run Phase 17 from any directory."""
import sys
import os

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
sys.path.insert(0, os.path.join(script_dir, "..", "..", "src"))
os.chdir(script_dir)

# Now import and run
import run_phase17
run_phase17.main()
