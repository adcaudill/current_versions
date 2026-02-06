#!/usr/bin/env python3
import json
import re
import sys
from collections import OrderedDict
from urllib.request import urlopen

JSON_PATH = "../current_versions.json"
PHP_DOWNLOADS_URL = "https://www.php.net/downloads.php?source=Y"

# Regex to match PHP version headers like <h3 id="v8.4.10" class="title"> ... PHP 8.4.10 ...
PHP_VERSION_HEADER_RE = re.compile(
    r'<h3 id="v(\d+\.\d+\.\d+)" class="title">.*?PHP (\d+\.\d+\.\d+)', re.DOTALL
)


def get_php_versions():
    try:
        with urlopen(PHP_DOWNLOADS_URL) as response:
            html = response.read().decode("utf-8")
        # Find all version headers
        matches = PHP_VERSION_HEADER_RE.findall(html)
        # OrderedDict to preserve order (latest first)
        versions = OrderedDict()
        for full, _ in matches:
            major_minor = ".".join(full.split(".")[:2])
            if major_minor not in versions:
                versions[major_minor] = full
        # The first match is the latest
        latest = matches[0][0] if matches else None
        return latest, versions
    except Exception as e:
        print(f"Error fetching PHP versions: {e}", file=sys.stderr)
        return None, {}


def update_json_with_php_versions(latest, series_versions):
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        php_data = data["software"].get("php", {})
        updated = False
        # Update latest
        if php_data.get("latest") != latest:
            php_data["latest"] = latest
            updated = True
        # Update or add series
        for series, version in series_versions.items():
            if php_data.get(series) != version:
                php_data[series] = version
                updated = True
        # Remove series that are no longer present
        for key in list(php_data.keys()):
            if key not in ["latest"] + list(series_versions.keys()):
                del php_data[key]
                updated = True
        data["software"]["php"] = php_data
        if updated:
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent="\t")
            print(f"Updated PHP versions: latest={latest}, series={series_versions}")
        else:
            print("PHP versions are already up to date.")
        return updated
    except Exception as e:
        print(f"Error updating JSON: {e}", file=sys.stderr)
        return False


def main():
    latest, series_versions = get_php_versions()
    if not latest or not series_versions:
        print("Could not determine PHP versions.", file=sys.stderr)
        sys.exit(1)
    update_json_with_php_versions(latest, series_versions)


if __name__ == "__main__":
    main()
