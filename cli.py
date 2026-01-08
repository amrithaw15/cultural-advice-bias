import argparse
import subprocess
import sys

REGION_TO_SCRIPT = {
    "filipino": "filipino_main_therapy_bias.py",
    "indian": "indian_main_therapy_bias.py",
    "nigerian": "nigerian_main_therapy_bias.py",
}

def run_region(region: str) -> int:
    script = REGION_TO_SCRIPT[region]
    print(f"\n=== Running region: {region} ({script}) ===")
    return subprocess.call([sys.executable, script])

def run_all_regions() -> int:
    for region in REGION_TO_SCRIPT:
        code = run_region(region)
        if code != 0:
            print(f"❌ Failed on region: {region}")
            return code
    print("\n✅ All regions completed.")
    return 0

def start_server() -> int:
    print("\n=== Starting visualization server ===")
    return subprocess.call([sys.executable, "start_server_fixs.py"])

def main():
    parser = argparse.ArgumentParser(
        description="Cultural Advice Bias – evaluation runner and visualization"
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run all regions and start visualization"
    )

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Start visualization ONLY (no evaluations)"
    )

    parser.add_argument(
        "--region",
        choices=["filipino", "indian", "nigerian"],
        help="Run evaluation for a single region ONLY (no visualization)"
    )

    args = parser.parse_args()

    # Enforce valid combinations
    if args.serve and (args.visualize or args.region):
        parser.error("--serve cannot be combined with --visualize or --region")

    if args.visualize and args.region:
        parser.error("--visualize cannot be combined with --region")

    if args.serve:
        code = run_all_regions()
        if code != 0:
            sys.exit(code)
        sys.exit(start_server())

    if args.visualize:
        sys.exit(start_server())

    if args.region:
        sys.exit(run_region(args.region))

    parser.error("You must specify one of: --serve, --visualize, or --region")

if __name__ == "__main__":
    main()
