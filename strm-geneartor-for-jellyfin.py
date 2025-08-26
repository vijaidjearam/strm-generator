import os
import re
import logging
import requests
from guessit import guessit
from pathlib import Path
import time
#Todo
# When transcodeLimitReached set the POLL_INTERVAL = 24 hrs

# ==== CONFIG ====
API_BASE = "https://debrid-link.com/api/v2"
# Override config with env vars
API_TOKEN = os.getenv("API_TOKEN", "")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "jellyfin_strm")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "3600"))  # default 1h

# === Allowed media types ===
MEDIA_EXTENSIONS = {
    '.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv',
    '.mp3', '.aac', '.flac', '.wav'
}

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "python-requests (debridlink-jellyfin)"
}

# === Logging Setup (console only) ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def clean_filename(filename: str) -> str:
    """Strip common site prefixes like 'www.tamil.blue - ' or [www.Site.com] etc."""
    cleaned = re.sub(
        r'^(?:\[\s*www\.[\w.-]+\s*\]|\(\s*www\.[\w.-]+\s*\)|www\.[\w.-]+)\s*-\s*',
        '',
        filename,
        flags=re.IGNORECASE
    )
    return cleaned.strip()


def sanitize_filename(name: str) -> str:
    """Remove filesystem-unsafe characters after cleaning."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def list_seedbox():
    """Fetch torrents/seedbox list (with files inside)."""
    url = f"{API_BASE}/seedbox/list"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    return data.get("value", [])


def get_transcode_url(file_id: str) -> str:
    """Start a transcode session and return the stream URL for a file.
       Returns 'QUOTA_REACHED' if quota exceeded."""
    url = f"{API_BASE}/stream/transcode/add"
    resp = requests.post(url, headers=HEADERS, json={"id": file_id})

    # Handle quota exhaustion
    if resp.status_code == 400:
        try:
            data = resp.json()
            if data.get("error") == "transcodeLimitReached":
                logging.error("Transcode quota reached (API returned transcodeLimitReached). Stopping.")
                return "QUOTA_REACHED"
        except Exception:
            logging.error("Transcode quota reached (HTTP 400). Stopping.")
            return "QUOTA_REACHED"

    if resp.status_code == 429:  # Too Many Requests
        logging.error("Transcode quota reached (HTTP 429). Stopping.")
        return "QUOTA_REACHED"

    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        logging.error(f"API refused transcode for {file_id}: {data}")
        return "QUOTA_REACHED"

    return data["value"].get("streamUrl")



def build_strm_path(file_name: str) -> Path:
    """Use guessit to build a Jellyfin-friendly path for .strm file."""
    cleaned_name = clean_filename(file_name)
    safe_name = sanitize_filename(cleaned_name)
    info = guessit(safe_name)

    title = sanitize_filename(info.get("title", "Unknown"))
    year = info.get("year")
    season = info.get("season")
    episode = info.get("episode")

    if info.get("type") == "episode" and season and episode:
        base = OUTPUT_DIR / "TVShows"
        folder = base / f"{title}{f' ({year})' if year else ''}" / f"Season {season:02d}"
        filename = f"{title} - S{season:02d}E{episode:02d}.strm"
        return folder / filename

    elif info.get("type") == "movie":
        base = OUTPUT_DIR / "Movies"
        folder = base / f"{title}{f' ({year})' if year else ''}"
        filename = f"{title}{f' ({year})' if year else ''}.strm"
        return folder / filename

    else:
        base = OUTPUT_DIR / "Others"
        filename = f"{safe_name}.strm"
        return base / filename


def generate_strm_files(limit=10):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    torrents = list_seedbox()
    logging.info(f"Found {len(torrents)} seedbox entries.")

    processed = 0

    for torrent in torrents:
        files = torrent.get("files", [])
        for f in files:
            if processed >= limit:
                logging.info(f"Reached test limit of {limit} files, stopping.")
                return

            file_id = f.get("id")
            file_name = f.get("name")

            ext = Path(file_name).suffix.lower()
            if ext not in MEDIA_EXTENSIONS:
                logging.info(f"Skipping (not a media file): {file_name}")
                continue

            if not f.get("downloaded"):
                logging.info(f"Skipping (not downloaded yet): {file_name}")
                continue

            strm_path = build_strm_path(file_name)

            if strm_path.exists():
                logging.info(f"Skipping (already exists): {strm_path}")
                continue

            logging.info(f"Processing: {file_name}")
            stream_url = get_transcode_url(file_id)

            if stream_url == "QUOTA_REACHED":
                logging.warning("Stopping loop due to transcode quota reached.")
                return

            if not stream_url:
                logging.error(f"Failed to get stream URL for {file_name}")
                continue

            strm_path.parent.mkdir(parents=True, exist_ok=True)
            with open(strm_path, "w", encoding="utf-8") as out:
                out.write(stream_url + "\n")

            logging.info(f"Created {strm_path}")
            processed += 1


if __name__ == "__main__":
    while True:
        generate_strm_files(limit=10)
        logging.info(f"Sleeping for {POLL_INTERVAL} seconds...")
        time.sleep(POLL_INTERVAL)


