"""Wrapper to run Phase 8-12 experiments with API key set."""
import os
import sys

# Set your OpenRouter API key
# os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-YOUR_KEY_HERE"

# Fix Windows encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)
os.chdir(src_dir)

# Import and run phases sequentially
phases = [8, 9, 10, 11, 12]

for phase_num in phases:
    print(f"\n{'='*70}")
    print(f"  PHASE {phase_num}")
    print(f"{'='*70}\n")
    try:
        mod = __import__(f"phase_{phase_num}.run_phase{phase_num}", fromlist=["main"])
        result = mod.main()
        print(f"\n  Phase {phase_num} completed. Result type: {type(result)}")
        if isinstance(result, dict):
            for k, v in result.items():
                if k not in ("experiments", "dialogues", "steps"):
                    print(f"    {k}: {v}")
    except Exception as e:
        print(f"  Phase {phase_num} FAILED: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*70}")
print("  ALL PHASES COMPLETE")
print(f"{'='*70}")
