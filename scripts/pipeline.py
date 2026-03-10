#!/usr/bin/env python3
"""
ZenBot Data Pipeline - Consolidated Script

Runs the entire data processing pipeline:
1. Fetch tickets from Zendesk
2. Clean and normalize data
3. Chunk tickets for RAG
4. Refine chunks (deduplicate, filter)
5. Generate embeddings
6. Upload to Qdrant

Usage:
    python3 scripts/pipeline.py --all                    # Run full pipeline
    python3 scripts/pipeline.py --from-step 5            # Resume from step 5
    python3 scripts/pipeline.py --steps 1,2,3            # Run specific steps
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

# ── Configuration ───────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

STEPS = {
    1: "Fetch tickets from Zendesk",
    2: "Clean and normalize tickets",
    3: "Chunk tickets for RAG",
    4: "Refine chunks (deduplicate)",
    5: "Generate embeddings",
    6: "Upload to Qdrant"
}

# ── Step 1: Fetch Tickets ───────────────────────────────────────────────────────
def step1_fetch_tickets():
    """Fetch tickets from Zendesk API."""
    print("\n" + "="*70)
    print("STEP 1: Fetching tickets from Zendesk")
    print("="*70)

    from fetch_tickets import main as fetch_main
    fetch_main()

    print("✅ Step 1 complete")


# ── Step 2: Clean Tickets ───────────────────────────────────────────────────────
def step2_clean_tickets():
    """Clean and normalize ticket data."""
    print("\n" + "="*70)
    print("STEP 2: Cleaning and normalizing tickets")
    print("="*70)

    from clean_tickets import main as clean_main
    clean_main()

    print("✅ Step 2 complete")


# ── Step 3: Chunk Tickets ───────────────────────────────────────────────────────
def step3_chunk_tickets():
    """Chunk tickets into RAG-ready pieces."""
    print("\n" + "="*70)
    print("STEP 3: Chunking tickets for RAG")
    print("="*70)

    from chunk_tickets import main as chunk_main
    chunk_main()

    print("✅ Step 3 complete")


# ── Step 4: Refine Chunks ───────────────────────────────────────────────────────
def step4_refine_chunks():
    """Refine chunks (deduplicate, filter short chunks)."""
    print("\n" + "="*70)
    print("STEP 4: Refining chunks")
    print("="*70)

    from refine_chunks import main as refine_main
    refine_main()

    print("✅ Step 4 complete")


# ── Step 5: Generate Embeddings ─────────────────────────────────────────────────
def step5_embed_chunks():
    """Generate embeddings using OpenAI."""
    print("\n" + "="*70)
    print("STEP 5: Generating embeddings")
    print("="*70)

    from embed_chunks import main as embed_main
    embed_main()

    print("✅ Step 5 complete")


# ── Step 6: Upload to Qdrant ────────────────────────────────────────────────────
def step6_upload_qdrant():
    """Upload embeddings to Qdrant vector database."""
    print("\n" + "="*70)
    print("STEP 6: Uploading to Qdrant")
    print("="*70)

    from upload_to_qdrant import main as upload_main
    upload_main()

    print("✅ Step 6 complete")


# ── Main Pipeline ───────────────────────────────────────────────────────────────
def run_pipeline(steps: List[int]):
    """Run specified pipeline steps."""
    step_functions = {
        1: step1_fetch_tickets,
        2: step2_clean_tickets,
        3: step3_chunk_tickets,
        4: step4_refine_chunks,
        5: step5_embed_chunks,
        6: step6_upload_qdrant
    }

    start_time = time.time()

    print("\n" + "="*70)
    print("🚀 ZenBot Data Pipeline")
    print("="*70)
    print(f"Running steps: {steps}")
    print()

    for step in steps:
        if step not in step_functions:
            print(f"❌ Invalid step: {step}")
            continue

        try:
            step_functions[step]()
        except Exception as e:
            print(f"\n❌ Step {step} failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"\nStopping pipeline at step {step}")
            sys.exit(1)

    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print(f"✅ Pipeline complete! Elapsed time: {elapsed:.1f}s")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="ZenBot Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/pipeline.py --all              # Run all steps
  python3 scripts/pipeline.py --from-step 5      # Resume from step 5
  python3 scripts/pipeline.py --steps 1,2,3      # Run steps 1, 2, 3
  python3 scripts/pipeline.py --steps 5,6        # Just embed & upload
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Run all steps')
    group.add_argument('--from-step', type=int, metavar='N', help='Run from step N to end')
    group.add_argument('--steps', type=str, metavar='1,2,3', help='Run specific steps (comma-separated)')

    args = parser.parse_args()

    # Determine which steps to run
    if args.all:
        steps = list(range(1, 7))
    elif args.from_step:
        if args.from_step < 1 or args.from_step > 6:
            print(f"❌ Invalid step number: {args.from_step}")
            sys.exit(1)
        steps = list(range(args.from_step, 7))
    else:  # args.steps
        try:
            steps = [int(s.strip()) for s in args.steps.split(',')]
            invalid = [s for s in steps if s < 1 or s > 6]
            if invalid:
                print(f"❌ Invalid step numbers: {invalid}")
                sys.exit(1)
        except ValueError:
            print(f"❌ Invalid steps format: {args.steps}")
            sys.exit(1)

    # Show plan
    print("\n📋 Pipeline Plan:")
    for step in steps:
        print(f"  {step}. {STEPS[step]}")
    print()

    # Run pipeline
    run_pipeline(steps)


if __name__ == "__main__":
    main()
