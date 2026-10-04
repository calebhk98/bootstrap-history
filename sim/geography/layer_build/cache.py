"""Download-once cache for public source datasets (kept outside the repo)."""
import os
import urllib.request
import zipfile

DEFAULT_CACHE = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "bootstrap-history", "geography-build")


def fetch(url, cache_dir, name=None):
    """Path of the cached file for `url`, downloading it on first use."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, name or url.rsplit("/", 1)[1])
    if not os.path.exists(path):
        print("  downloading %s" % url)
        request = urllib.request.Request(url, headers={"User-Agent": "bootstrap-history-geography-build/1.0"})
        with urllib.request.urlopen(request, timeout=300) as response, open(path + ".part", "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(path + ".part", path)
    return path


def fetch_unzipped(url, cache_dir):
    """Directory holding the extracted contents of the zip at `url`."""
    archive = fetch(url, cache_dir)
    directory = archive[:-len(".zip")] + "_unzipped"
    if not os.path.isdir(directory):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(directory)
    return directory
