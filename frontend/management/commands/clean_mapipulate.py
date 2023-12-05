from django.core.management.base import BaseCommand
from frontend.models import SpotifyUser, CurrentVotes
import random
import requests
from django.db.models import Count

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        users = SpotifyUser.objects.all()

        for user in users:
            access_token = user.spotify_access_token
            current_playback = get_current_playback(access_token)

            if current_playback:
                current_song_id = extract_current_song_id(current_playback)
                playlist_id = get_playlist_id(access_token)
                most_voted_song = get_most_voted_song()
                
                if playlist_id and most_voted_song and current_song_id:
                    # Remove the voted song from the playlist
                    remove_voted_song_from_playlist(access_token, playlist_id, most_voted_song)
                    
                    # Get the index of the currently playing song in the playlist
                    current_song_index = get_current_song_index(access_token, playlist_id, current_song_id)
                    
                    if current_song_index != -1:
                        # Insert the voted song after the currently playing song
                        insert_song_after_current(playlist_id, access_token, playlist_id, most_voted_song, current_song_index + 1)

        # Clear all rows in the CurrentVotes table
        CurrentVotes.objects.all().delete()


def get_current_playback(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    endpoint = 'https://api.spotify.com/v1/me/player/currently-playing'
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        return response.json()
    return None


def extract_current_song_id(current_playback):
    return current_playback.get('item', {}).get('id') if current_playback else None


def get_playlist_id(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    endpoint = 'https://api.spotify.com/v1/me/playlists'
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        playlists = response.json().get('items', [])
        for playlist in playlists:
            if playlist['name'] == 'voting_playlist':
                return playlist['id']
    return None


def remove_voted_song_from_playlist(access_token, playlist_id, song_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    data = {
        'tracks': [{'uri': f'spotify:track:{song_id}'}]
    }

    response = requests.delete(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        print('Song removed from the playlist!')
    else:
        print('Failed to remove song:', response.text)


def get_most_voted_song(user):
    # Get the most voted song based on the user's criteria
    user_votes = CurrentVotes.objects.filter(cafe=user).values('spotify_music_id').annotate(vote_count=Count('spotify_music_id')).order_by('-vote_count')
    
    if user_votes.exists():
        max_votes = user_votes.first()['vote_count']
        top_songs = user_votes.filter(vote_count=max_votes)
        most_voted_song = random.choice(top_songs)['spotify_music_id']
        return most_voted_song
    return None


def get_current_song_index(access_token, current_song_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    playlist_id = 'your_playlist_id'
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        tracks = response.json().get('items', [])
        for index, track in enumerate(tracks):
            if track['track']['id'] == current_song_id:
                return index
    return -1


def insert_song_after_current(playlist_id, access_token, song_to_insert, position):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    data = {
        'uris': [f'spotify:track:{song_to_insert}'],
        'position': position
    }

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code == 201:
        print('Song inserted successfully!')
    else:
        print('Failed to insert song:', response.text)
