# Arr Cleanup Script

This script checks for failed downloads in qBittorrent and marks them as failed in Sonarr and Radarr. It ensures that unavailable media is properly blocked or removed based on configurable conditions such as availability, time since added, and active hours. The script is particularly useful for automating media management by cleaning up failed downloads and ensuring that they are handled in your media library.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Logs](#logs)
- [Usage](#usage)
- [Example Output](#example-output)
- [Troubleshooting](#troubleshooting)

## Features

- Automatically identifies torrents that have stalled or are missing pieces.
- Marks corresponding episodes in Sonarr or movies in Radarr as failed.
- Removes torrents from qBittorrent based on customizable conditions.
- Configurable settings for availability, active time, and more.
- Log output for detailed tracking of the script's actions.

## Requirements

- Python 3.x
- `requests` library (Install via `pip install requests`)

## Setup

1. Clone the repository or download the script.
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Configure the script by editing the following parameters inside the script:

   - **qBittorrent Configuration:**

     ```python
     QB_URL = "http://localhost:8090/api/v2/"  # Update with your qBittorrent URL
     QB_USER = "admin"                         # Replace with your qBittorrent username
     QB_PASSWORD = "changeme"                  # Replace with your qBittorrent password
     ```

   - **Sonarr Configuration:**

     ```python
     SONARR_ENABLED = True
     SONARR_URL = "http://xxx.xxx.x.xxx:8989/api/v3/"
     SONARR_API_KEY = "API_KEY"                # Replace with your Sonarr API key
     ```

   - **Radarr Configuration:**
     ```python
     RADARR_ENABLED = True
     RADARR_URL = "http://xxx.xxx.x.xxx:7878/api/v3/"
     RADARR_API_KEY = "API_KEY"                # Replace with your Radarr API key
     ```

4. Customize behavior by setting the following parameters:

   - **Torrent Removal:**

     ```python
     QB_ALWAYS_REMOVE = False   # Always remove failed torrents, regardless of Sonarr or Radarr check
     QB_REMOVE_IF_KNOWN = True  # Only remove failed torrents if found in Sonarr or Radarr
     ```

   - **Torrent Filtering:**
     ```python
     MIN_AVAILABILITY = 1.0     # Minimum availability threshold (Recommended: 1.0 for 100%)
     MIN_ACTIVE_HOURS = 24      # Minimum active time before considering availability (e.g., 24 hours)
     MIN_ADDED_HOURS = 0        # Minimum time since torrent was added (e.g., 0 hours)
     ```

## How It Works

1. The script authenticates with qBittorrent using the provided credentials.
2. It retrieves the list of torrents and filters for stalled or failed downloads based on availability and time conditions.
3. It checks whether the failed torrent corresponds to an episode in Sonarr or a movie in Radarr:
   - For Sonarr, it uses the torrent title to parse and search for the episode.
   - For Radarr, it looks up the movie using the torrent title.
4. If a corresponding episode or movie is found, the script marks the item as failed in Sonarr or Radarr.
5. Optionally, the torrent is removed from qBittorrent based on the specified conditions.

## Logs

The script logs all actions and decisions in a log file named `arrCleanUp.log`, including:

- Authentication status
- Failed torrents found
- Media matched in Sonarr or Radarr
- Actions taken (marked as failed, removed from qBittorrent)

## Usage

Run the script via command line:

```bash
python arrCleanUp.py
```

### Cron Job

To automate the script, set up a cron job to run it at regular intervals. For example, to run the script every 6 hours, use the following command:

```bash
0 */6 * * * /usr/bin/python3 /path/to/arrCleanUp.py
```

## Example Output

    2024-01-01 13:45:01,901 - INFO - Found 1 failed torrents in qBittorrent above threshold.
    2024-01-01 13:45:01,901 - WARNING - ---> Processing 'File.mkv'
    2024-01-01 13:45:01,902 - INFO - Current availability: 5.30%
    2024-01-01 13:45:01,902 - INFO - Active download time: 24.41 hour(s)
    2024-01-01 13:45:01,902 - INFO - Media added 24.41 hour(s) ago
    2024-01-01 13:45:01,902 - INFO - Checking Sonarr...
    2024-01-01 13:45:01,908 - WARNING - No episode found for title: File.mkv
    2024-01-01 13:45:01,912 - INFO - Checking Radarr...
    2024-01-01 13:45:02,551 - INFO - Found movie ID 1234
    2024-01-01 13:45:02,562 - INFO - Successfully added the torrent to the blocklist in Radarr.
    2024-01-01 13:45:02,566 - INFO - Successfully removed 'File.mkv' from qBittorrent downloads.
    2024-01-01 13:45:02,566 - INFO - Cleanup completed.

## Troubleshooting

Ensure that Sonarr and Radarr are accessible via the provided URLs and API keys.
Check the arrCleanUp.log for detailed logs of the script’s operations.
Verify that qBittorrent is running and the API is enabled in its settings.
