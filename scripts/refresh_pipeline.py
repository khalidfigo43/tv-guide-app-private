import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path


def run_step(step_name, cmd):
    print("\n" + "=" * 80)
    print(f"PIPELINE STEP: {step_name}")
    print("=" * 80)
    print(f"Executing: {cmd}")
    
    start_time = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    elapsed = time.time() - start_time
    
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
        
    if res.returncode != 0:
        print(f"❌ Step '{step_name}' failed with return code {res.returncode}")
        return False
        
    print(f"✓ Step '{step_name}' completed in {elapsed:.2f}s")
    return True


def main():
    print("=" * 80)
    print("STARTING AUTOMATED TV GUIDE DATA REFRESH PIPELINE")
    print("Timestamp:", datetime.now().isoformat())
    print("=" * 80)

    python_bin = sys.executable

    # Step 1: Run Rotana Collector
    if not run_step("Rotana Collector", f'"{python_bin}" -X utf8 collectors/rotana/collector.py'):
        print("Collector run failed.")
        return

    # Step 2: Validate Data Quality
    if not run_step("Schedule Data Validation", f'"{python_bin}" -X utf8 collectors/rotana/validate.py'):
        print("Validation step failed.")
        return

    # Step 3: Multi-Network Schedules Generation (115 Channels)
    if not run_step("Multi-Network 115 Channels Schedule Builder", f'"{python_bin}" -X utf8 collectors/network_schedules.py'):
        print("Network schedule generation failed.")
        return

    # Step 4: ElCinema Live TV Guide Collector (MBC, OSN, Nile, etc.)
    if not run_step("ElCinema Live TV Guide Collector", f'"{python_bin}" -X utf8 collectors/elcinema_collector.py'):
        print("ElCinema live collection failed.")

    # Step 5: TMDB Titles Enrichment (Movies, Series, Documentaries)
    if not run_step("TMDB Metadata Enrichment", f'"{python_bin}" -X utf8 enrich_all_titles.py'):
        print("Metadata enrichment failed.")
        return

    # Step 6: Supabase Seed Generation
    if not run_step("Generate Supabase Seed SQL", f'"{python_bin}" -X utf8 scripts/generate_seed_sql.py'):
        print("Seed generation failed.")
        return

    # Step 7: Run API Verification Tests
    if not run_step("API Health & Verification Tests", f'"{python_bin}" -X utf8 test_backend_api.py'):
        print("API test failed.")
        return

    print("\n" + "=" * 80)
    print("🎉 FULL TV GUIDE PIPELINE REFRESH COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()

