import sys
import os
import time
from pathlib import Path

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.data_fetcher import MFDataFetcher, TOP_FUNDS_REGISTRY
from app.core.logger import get_logger

logger = get_logger("pre_warm_cache")

def main():
    fetcher = MFDataFetcher()
    total = len(TOP_FUNDS_REGISTRY)
    
    logger.info(f"Starting Institutional Cache Pre-warm for {total} funds...")
    
    success_count = 0
    fail_count = 0
    
    # 1. First, fetch all schemes index
    try:
        fetcher.get_all_schemes()
        logger.info("✅ Scheme index primed.")
    except Exception as e:
        logger.error(f"❌ Failed to prime scheme index: {e}")

    # 2. Iterate through high-priority registry
    for i, (code, name) in enumerate(TOP_FUNDS_REGISTRY.items(), 1):
        try:
            logger.info(f"[{i}/{total}] Warming: {name} ({code})...")
            # This triggers the API fetch and persistence to data/cache/{code}.csv
            fetcher.get_nav_history(code)
            success_count += 1
            # Rate limiting protection
            time.sleep(1.5)
        except Exception as e:
            logger.error(f"   FAILED {code}: {e}")
            fail_count += 1

    logger.info(f"Pre-warm Complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    main()
