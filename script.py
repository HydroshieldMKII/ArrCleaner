# Description: This script will check for failed downloads in qBittorrent and mark them as failed in Sonarr and Radarr.

import requests
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(filename='arrCleanUp.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Configuration
QB_URL = "http://localhost:8090/api/v2/"
QB_USER = "admin"            # Replace with your qBittorrent username
QB_PASSWORD = "changeme"     # Replace with your qBittorrent password

QB_ALWAYS_REMOVE = False      #Always remove failed torrent from download, even if not found in Sonarr or Radarr
QB_REMOVE_IF_KNOWN = True   #Only remove failed torrent if an ID as been found in Sonarr or Radarr. Note: this will remove fill in qBittorrent even if the media was not successfully block 

SONARR_ENABLED = True
SONARR_URL = "http://xxx.xxx.x.xxx:8989/api/v3/"
SONARR_API_KEY = "API_KEY"  # Replace with your Sonarr API key

RADARR_ENABLED = True
RADARR_URL = "http://xxx.xxx.x.xxx:7878/api/v3/"
RADARR_API_KEY = "API_KEY"  # Replace with your Radarr API key

MIN_AVAILABILITY = 1.0   # Minimum availability a file must have. Recommended 1.0 (eg. 1.0 = 100%, 0.25 = 25%, At least X% of the file is available across all peers)
MIN_ACTIVE_HOURS = 24     # Minimum active time of a torrent in hour before considering availability. This can help improve accuracy.(eg. 2 = 2 hours, Torrent must be active for at least X hours)
MIN_ADDED_HOURS = 0      # Minimum hours since the torrent was added before considering availability. The file must have been added for at least X hours. (eg. 0 = 0 hours, Torrent must be at least X hours old)

# Function to authenticate with qBittorrent
def authenticate_qbittorrent():
    session = requests.Session()
    response = session.post(f"{QB_URL}auth/login", data={"username": QB_USER, "password": QB_PASSWORD})
    #logging.info("Logging in to qBittorrent instance...")

    if response.status_code == 200 and response.text.strip() == "Ok.":
        return session
    else:
        logging.error("Something went wrong while authenticating on qBittorrent instance. Response Status Code: %s - Response Text: %s", response.status_code, response.text)
        return False

# Function to get failed torrents from qBittorrent
def get_failed_torrents(session):
    response = session.get(f"{QB_URL}torrents/info")
    torrents = response.json()

    # Get the current time
    now = datetime.now()

    # Filter torrents based on availability, added time and active time
    failed_torrents = []
    for t in torrents:
        added_time = round((datetime.now() - datetime.fromtimestamp(t['added_on'])).total_seconds() / 3600, 2)
        active_time_hours = t['time_active'] / 3600
        torrent_state = t['state']

        # Filter torrents that are not fully available and have a minimum active time
        if abs(t['availability']) < MIN_AVAILABILITY and added_time >= MIN_ADDED_HOURS and active_time_hours >= MIN_ACTIVE_HOURS and torrent_state == 'stalledDL':
            failed_torrents.append(t)

    return failed_torrents


# Function to get Sonarr episode ID from torrent title
def get_episode_id(title):
    response = requests.get(f"{SONARR_URL}parse?title={title}", headers={"X-Api-Key": SONARR_API_KEY})
    data = response.json()
    
    # Debugging information
    #logging.debug("Parse API Response: %s", data)

    # Check if 'episodes' is in the data and has items
    if 'episodes' in data and len(data['episodes']) > 0:
        return data['episodes'][0]['id']
    else:
        logging.warning("No episode found for title: %s", title)
        return None

# Function to get Radarr movie ID from movie title
def get_movie_id(title):
    response = requests.get(f"{RADARR_URL}movie/lookup?term={title}", headers={"X-Api-Key": RADARR_API_KEY})
    data = response.json()
    
    # Debugging information
    #logging.debug("Radarr Movie Lookup Response: %s", data)

    if len(data) > 0:
        return data[0]['id']
    else:
        logging.warning("No movie found for title: %s", title)
        return None

# Function to get the history record ID for a given episode ID
def get_history_record_id(episode_id):
    response = requests.get(f"{SONARR_URL}history?sortKey=date&sortDir=desc&episodeId={episode_id}", headers={"X-Api-Key": SONARR_API_KEY})
    history = response.json()

    # Find the record ID of the 'grabbed' event
    return next((record['id'] for record in history['records'] if record['eventType'] == 'grabbed'), None)

# Function to mark a download as failed in Sonarr
def mark_as_failed_sonarr(record_id):
    response = requests.post(f"{SONARR_URL}history/failed/{record_id}", headers={"X-Api-Key": SONARR_API_KEY, "Content-Length": "0", "Content-Type": "application/json"})

    if response.status_code == 200:
        return True
    else:
        logging.error("Something went wrong while marking media as failed in Sonarr. Response Status Code: %s - Response Text: %s", response.status_code, response.text)
        return False

# Function to mark a movie as failed in Radarr
def mark_as_failed_radarr(movie_id):
    response = requests.post(f"{RADARR_URL}history/failed/{movie_id}", headers={"X-Api-Key": RADARR_API_KEY, "Content-Length": "0", "Content-Type": "application/json"})

    if response.status_code == 200:
        return True
    else:
        logging.error("Something went wrong while marking media as failed in Radarr. Response Status Code: %s - Response Text: %s", response.status_code, response.text)
        return False

# Function to remove a torrent from qBittorrent
def remove_torrent(session, torrent_hash):
    response = session.post(f"{QB_URL}torrents/delete", data={"hashes": torrent_hash, "deleteFiles": "true"})

    if response.status_code == 200:
        return True
    else:
        logging.error("Something went wrong while removing torrent from qBittorrent. Response Status Code: %s - Response Text: %s", response.status_code, response.text)
        return False

def main():
    # Authenticate with qBittorrent
    qb_session = authenticate_qbittorrent()

    # Get failed torrents from qBittorrent
    failed_torrents = get_failed_torrents(qb_session)
    
    logging.info("Found %s failed torrents in qBittorrent above threshold.", len(failed_torrents))

    for torrent in failed_torrents:
        title = torrent['name']
        torrent_hash = torrent['hash']
        availability = abs(round(round(torrent['availability'], 4) * 100, 4))  # File availability as a percentage
        active_time_hours = round(torrent['time_active'] / 3600, 2)
        added_time_hours = round((datetime.now() - datetime.fromtimestamp(torrent['added_on'])).total_seconds() / 3600, 2)

        logging.warning("---> Processing '%s'", title)
        logging.info("Current availability: %.2f%%", availability)
        logging.info("Active download time: %.2f hour(s)", active_time_hours)
        logging.info("Media added %.2f hour(s) ago", added_time_hours)

        media_found = False

        if SONARR_ENABLED:
            logging.info("Checking Sonarr...")
            episode_id = get_episode_id(title)
            if episode_id:
                logging.info("Found episode ID %s", episode_id)
                record_id = get_history_record_id(episode_id)  # Assign value to record_id
                media_found = True
                
                if record_id:
                    logging.info("Found history record ID %s", record_id)
                    if mark_as_failed_sonarr(record_id):
                        logging.info("Successfully added the torrent to the blocklist in Sonarr.")
                    else:
                        logging.error("Failed to add the torrent to the blocklist in Sonarr.")
                else:
                    logging.error("No history record found for '%s'.", title)
                
            
        if RADARR_ENABLED and not media_found:
            logging.info("Checking Radarr...")
            movie_id = get_movie_id(title)
            if movie_id:
                logging.info("Found movie ID %s", movie_id)
                success = mark_as_failed_radarr(movie_id)
                media_found = True
                
                if success:
                    logging.info("Successfully added the torrent to the blocklist in Radarr.")
                else:
                    logging.error("Failed to add the torrent to the blocklist in Radarr.")
            
        if not media_found:
            logging.critical("No media found for '%s'. No action taken.", title)

        # Remove the torrent from qBittorrent
        if QB_ALWAYS_REMOVE or (QB_REMOVE_IF_KNOWN and media_found):
            if remove_torrent(qb_session, torrent_hash):
                logging.info("Successfully removed '%s' from qBittorrent downloads.", title)
            else:
                logging.error("Failed to remove '%s' from qBittorrent downloads.", title)

    logging.info("Cleanup completed.")


if __name__ == "__main__":
    main()