import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# The 'scope' determines what permissions our app is asking for.
# 'user-read-playback-state' is needed to see available devices.
# 'user-modify-playback-state' is needed to control playback.
SCOPE = "user-read-playback-state user-modify-playback-state"

def get_spotify_client():
    """
    Authenticates with Spotify using credentials from environment variables.
    Handles the OAuth 2.0 flow and token caching.
    """
    # Spotipy will automatically look for the environment variables:
    # SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI
    try:
        auth_manager = SpotifyOAuth(scope=SCOPE)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # A quick check to see if authentication is working
        sp.current_user()
        
        return sp
    except Exception as e:
        print(f"Error authenticating with Spotify: {e}")
        print("Please ensure you have set the SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI environment variables.")
        return None

def play_playlist(playlist_uri):
    """
    Starts playing a specific playlist on the user's active Spotify device.
    
    :param playlist_uri: The URI of the playlist to play. 
                         (e.g., 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M')
    """
    sp = get_spotify_client()
    if not sp:
        print("Could not get Spotify client. Aborting.")
        return

    try:
        # Check for active devices
        devices = sp.devices()
        if not devices or not devices['devices']:
            print("No active Spotify device found. Please start playing on a device first.")
            return
            
        # Find the first active device
        active_device_id = None
        for device in devices['devices']:
            if device['is_active']:
                active_device_id = device['id']
                break
        
        if not active_device_id:
            # If no device is "active", pick the first one available.
            active_device_id = devices['devices'][0]['id']
            print("No active device, using the first one found.")

        # Start playback
        sp.start_playback(device_id=active_device_id, context_uri=playlist_uri)
        print(f"Started playing playlist {playlist_uri} on device {active_device_id}.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            print("No active device found. Please open Spotify on one of your devices.")
        elif e.http_status == 403:
            print("Playback failed. This may be due to the account being a free-tier user.")
        else:
            print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example of how to run this directly for testing:
if __name__ == '__main__':
    # Replace this with the URI of a playlist you want to test with
    # To get a playlist URI: Right-click playlist in Spotify -> Share -> Copy Spotify URI
    test_playlist_uri = 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M' # Example: "Today's Top Hits"
    play_playlist(test_playlist_uri)
