"""Downloads official, peer-reviewed scientific report PDFs directly from source institutions."""

import os
import sys
import logging
from pathlib import Path
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daaruka.download_real_corpus")

RAW_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"

REAL_SOURCES = [
    {
        "key": "cbd_cop15_dec_04",
        "title": "CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework",
        "url": "https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf",
        "filename": "cbd_cop15_dec_04.pdf",
        "publisher": "Convention on Biological Diversity (CBD / UNEP)",
        "year": 2022,
        "topics": ["policy", "restoration", "biodiversity-targets", "conservation"],
    },
    {
        "key": "ipcc_ar6_wg2_chapter02",
        "title": "IPCC AR6 WGII Chapter 2: Terrestrial and Freshwater Ecosystems and their Services",
        "url": "https://www.ipcc.ch/report/ar6/wg2/downloads/report/IPCC_AR6_WGII_Chapter02.pdf",
        "filename": "ipcc_ar6_wg2_chapter02.pdf",
        "publisher": "Intergovernmental Panel on Climate Change (IPCC)",
        "year": 2022,
        "topics": ["climate", "biodiversity", "ecosystems", "tipping-points", "resilience"],
    },
    {
        "key": "fao_recarbonizing_global_soils_vol3",
        "title": "FAO & ITPS Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
        "url": "https://www.fao.org/3/cb6595en/cb6595en.pdf",
        "filename": "fao_recarbonizing_global_soils_vol3.pdf",
        "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
        "year": 2021,
        "topics": ["soil", "carbon", "cover-cropping", "agriculture", "soc", "tillage"],
    },
]


def download_file(url: str, dest_path: Path, timeout: float = 120.0) -> int:
    """Download file streaming with standard browser headers, returning written bytes."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/pdf,*/*",
    }
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=timeout) as response:
        response.raise_for_status()
        total_bytes = 0
        with open(dest_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
        return total_bytes


def main():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Target directory for raw PDFs: {RAW_DATA_DIR}")

    results = []
    for item in REAL_SOURCES:
        dest_file = RAW_DATA_DIR / item["filename"]
        logger.info(f"Downloading '{item['title']}' from {item['url']} ...")
        try:
            bytes_written = download_file(item["url"], dest_file)
            size_mb = bytes_written / (1024 * 1024)
            logger.info(f"  [OK] Saved {item['filename']} -> {bytes_written:,} bytes ({size_mb:.2f} MB)")
            results.append({"name": item["filename"], "bytes": bytes_written, "status": "SUCCESS"})
        except Exception as e:
            logger.error(f"  [FAIL] Could not download {item['filename']}: {e}")
            results.append({"name": item["filename"], "bytes": 0, "status": f"FAILED: {e}"})

    print("\n--- DOWNLOAD SUMMARY ---")
    for r in results:
        print(f"{r['name']}: {r['status']} ({r['bytes']:,} bytes)")


if __name__ == "__main__":
    main()
