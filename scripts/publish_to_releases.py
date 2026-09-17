import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

RELEASES_REPO = "khalidfigo43/tv-guide-releases"


def run_cmd(cmd, cwd=None, mask=None):
    display_cmd = cmd
    if mask:
        display_cmd = display_cmd.replace(mask, "***")
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        err = res.stderr.replace(mask, "***") if mask else res.stderr
        print(f"Command failed: {display_cmd}\nError: {err}")
    return res.returncode == 0, res.stdout, res.stderr


def publish():
    schedules_src = Path("data/schedules.json")
    metadata_src = Path("data/metadata.json")

    if not schedules_src.exists():
        print("❌ Error: data/schedules.json does not exist. Run pipeline first.")
        sys.exit(1)

    token = os.getenv("RELEASES_TOKEN") or os.getenv("GH_PAT")
    temp_dir = tempfile.mkdtemp(prefix="tvguide_releases_")

    try:
        if token:
            clone_url = f"https://x-access-token:{token}@github.com/{RELEASES_REPO}.git"
            print(f"[*] Cloning https://github.com/{RELEASES_REPO} using secure token...")
            ok, _, _ = run_cmd(f"git clone --depth 1 {clone_url} .", cwd=temp_dir, mask=token)
        else:
            print(f"[*] No RELEASES_TOKEN found. Attempting clone using system Git credentials...")
            clone_url = f"https://github.com/{RELEASES_REPO}.git"
            ok, _, _ = run_cmd(f"git clone --depth 1 {clone_url} .", cwd=temp_dir)

        if not ok:
            if os.getenv("GITHUB_ACTIONS"):
                print(f"⚠️ [NOTICE] Cannot push to {RELEASES_REPO}: RELEASES_TOKEN secret is not configured in GitHub repository secrets.")
                print("   Please create a personal access token with repo write access and add it as RELEASES_TOKEN.")
                return False
            else:
                print("❌ Could not clone releases repository.")
                return False

        # Copy data files
        dest_data_dir = Path(temp_dir) / "data"
        dest_data_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schedules_src, dest_data_dir / "schedules.json")
        if metadata_src.exists():
            shutil.copy2(metadata_src, dest_data_dir / "metadata.json")
        programs_src = Path("data/programs.json")
        if programs_src.exists():
            shutil.copy2(programs_src, dest_data_dir / "programs.json")
        channels_src = Path("data/channels.json")
        if channels_src.exists():
            shutil.copy2(channels_src, dest_data_dir / "channels.json")
        deltas_src = Path("data/deltas")
        if deltas_src.exists():
            dest_deltas_dir = dest_data_dir / "deltas"
            dest_deltas_dir.mkdir(parents=True, exist_ok=True)
            for df in deltas_src.glob("*.json"):
                shutil.copy2(df, dest_deltas_dir / df.name)

        # Git commit and push
        run_cmd('git config user.name "github-actions[bot]"', cwd=temp_dir)
        run_cmd('git config user.email "github-actions[bot]@users.noreply.github.com"', cwd=temp_dir)
        run_cmd("git add data/", cwd=temp_dir)

        ok_diff, out_diff, _ = run_cmd("git diff --staged --quiet", cwd=temp_dir)
        if ok_diff:
            print("✓ No changes detected in releases repository (already up to date).")
            return True

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_msg = f"chore(data): automated daily schedules sync [{now_str}]"
        ok_commit, _, _ = run_cmd(f'git commit -m "{commit_msg}"', cwd=temp_dir)
        if not ok_commit:
            print("Commit failed.")
            return False

        print(f"[*] Pushing updated schedules to https://github.com/{RELEASES_REPO}...")
        ok_push, _, err_push = run_cmd("git push origin main", cwd=temp_dir, mask=token if token else None)
        if ok_push:
            print(f"[+] Successfully published schedules.json and metadata.json to https://github.com/{RELEASES_REPO}!")
            return True
        else:
            print("Push failed.")
            return False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = publish()
    if not success and os.getenv("GITHUB_ACTIONS") and not os.getenv("RELEASES_TOKEN"):
        sys.exit(0)
    elif not success:
        sys.exit(1)

