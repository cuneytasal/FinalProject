#from requests_toolbelt.utils import dump
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, RegisterForm
from .credentials import REDIRECT_URI, CLIENT_SECRET, CLIENT_ID
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SpotifyUser, MusicVotes, CafeMusics, CurrentVotes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.core.cache import cache
from urllib.parse import urlencode
import secrets
import requests
import time
from datetime import datetime, timedelta



def loginUser(request):
    form = LoginForm()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        #print(user)
        if user is not None:
            login(request, user)
            return redirect('spotify_auth')
        else:
            # If authentication fails, add an error message to the context
            messages.error(request, 'Username or password is incorrect. Please try again.')

    context = {'form': form}
    return render(request, 'frontend/index.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


def registerUser(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            cafe_name = form.cleaned_data['cafe_name']
            name = form.cleaned_data['name_surname']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            desired_password = form.cleaned_data['password']
            
            subject = 'New cafe owner'
            content = f"{cafe_name}\n{desired_password}{name}\n{email}\n{phone_number}"

            html = render_to_string('emails/contactForm.html', {
                'name': name,
                'email': email,
                'phone_number': phone_number,
                'cafe_name': cafe_name,
                'desired_password': desired_password
            })

            #send_mail(subject, content, 'music_voting@musicvoting.com', ['20171701035@stu.khas.edu.tr', 'ceren.durna@stu.khas.edu.tr'], html_message=html)
            send_mail(subject, content, 'music_voting@musicvoting.com', ['20171701035@stu.khas.edu.tr'], html_message=html)
            messages.success(request, 'Thank you for registering. We will get back to you as soon as possible.')
            return redirect('login')  # Redirect to login page after successful registration
        else:
            form = RegisterForm()

    context ={'form': form}
    return render(request, 'frontend/register.html', context)


@login_required(login_url="login")
def home(request):
    # Retrieve the user info including cafe_name
    User = get_user_model()
    user_info = User.objects.get(pk=request.user.pk)
    user_spotify = SpotifyUser.objects.get(user=user_info.pk)
    access_token = user_spotify.spotify_access_token
    #print(access_token)
    cafe_name = user_info.cafe_name
    cafe_id = user_info.pk

    playlists = []

    if access_token:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        playlist_url = 'https://api.spotify.com/v1/me/playlists'
        response = requests.get(playlist_url, headers=headers)

        #print(headers)
        #print(dump.dump_all(response).decode("utf-8"))
        
        if response.status_code == 200:
            playlists_data = response.json().get('items', [])
            
            for playlist in playlists_data:
                if playlist['name'] == 'voting_playlist':
                    continue
                else:
                    name = playlist['name']
                    images = playlist['images']
                    playlist_id = playlist['id']
                    if images:
                        image_url = images[0]['url']
                        playlists.append({'name': name, 'image_url': image_url, 'playlist_id': playlist_id})
        
    return render(request, 'frontend/home.html', {'playlists': playlists, 'cafe_name': cafe_name, 'cafe_id': cafe_id})


@login_required(login_url="login")
def playlist_songs(request, playlist_id):
    try:
        user_spotify = SpotifyUser.objects.get(user=request.user)
        access_token = user_spotify.spotify_access_token
        User = get_user_model()
        user_info = User.objects.get(pk=request.user.pk)  # Retrieve the user info including cafe_name
        cafe_name = user_info.cafe_name
        cafe_id = user_info.pk
    except SpotifyUser.DoesNotExist:
        access_token = None

    songs = []
    #playlist_name = "Playlist"  # Default playlist name in case fetching fails or not available

    if access_token:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
        response = requests.get(playlist_tracks_url, headers=headers)
        
        if response.status_code == 200:
            playlist_data = response.json()
            tracks_data = playlist_data.get('tracks', {}).get('items', [])
            for track in tracks_data:
                song_id = track['track']['id']  # Extract track ID
                name = track['track']['name']  # Extract track name
                artist = track['track']['artists'][0]['name']  # Extract artist name

                # Use track ID to fetch additional song details including images
                track_url = f'https://api.spotify.com/v1/tracks/{song_id}'
                track_response = requests.get(track_url, headers=headers)
                if track_response.status_code == 200:
                    track_info = track_response.json()
                    images = track_info['album']['images']
                    if images:
                        image_url = images[0]['url']  # Use the first image URL
                        songs.append({'name': name, 'artist': artist, 'image_url': image_url})
                    else:
                        songs.append({'name': name, 'artist': artist, 'image_url': None})
                else:
                    # Handle error fetching track details
                    pass
        
        if playlist_id:
            start_playback(access_token, playlist_id)
        
    return render(request, 'frontend/playlist_songs.html', {'songs': songs, 'cafe_name': cafe_name, 'cafe_id': cafe_id})


def start_playback(access_token, playlist_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        'context_uri': f'spotify:playlist:{playlist_id}',
        'offset': {'position': 0},  # Start from the beginning of the playlist
        'position_ms': 0            # Start at the beginning of the first track
    }

    devices_url = 'https://api.spotify.com/v1/me/player/devices'
    devices_response = requests.get(devices_url, headers=headers)

    if devices_response.status_code == 200:
        devices_data = devices_response.json().get('devices', [])
        if devices_data:
            device_id = devices_data[0]['id']  # Select the first available device
            playback_url = f'https://api.spotify.com/v1/me/player/play?device_id={device_id}'
            response = requests.put(playback_url, headers=headers, json=data)

            if response.status_code == 204:
                print('Playback started.')
                # Set repeat mode for the playlist
                time.sleep(3)
                set_repeat_mode(access_token, 'context')
                return True
            else:
                print('Failed to start playback:', response.json())
        else:
            print('No available devices found.')
    else:
        print('Failed to fetch devices:', devices_response.json())

    return False


def set_repeat_mode(access_token, repeat_state):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        'state': repeat_state  # Options: 'track', 'context', 'off'
    }

    repeat_url = 'https://api.spotify.com/v1/me/player/repeat'
    response = requests.put(repeat_url, headers=headers, params=data)

    if response.status_code == 204:
        print(f'Repeat mode set to {repeat_state}.')
        return True
    else:
        print('Failed to set repeat mode:', response.json())
        return False


@login_required(login_url="login")
def copy_playlist_and_rename(request, playlist_id):
    try:
        user_spotify = SpotifyUser.objects.get(user=request.user)
        access_token = user_spotify.spotify_access_token
    except SpotifyUser.DoesNotExist:
        access_token = None

    if access_token:
        user_playlists_url = 'https://api.spotify.com/v1/me/playlists'
        playlists_response = requests.get(user_playlists_url, headers={'Authorization': f'Bearer {access_token}'})

        if playlists_response.status_code == 200:
            user_playlists = playlists_response.json().get('items', [])
            voting_playlist_id = None
            playlist_list = []

            # Retrieve tracks from the selected playlist
            playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            response = requests.get(playlist_tracks_url, headers={'Authorization': f'Bearer {access_token}'})

            # Find the 'voting_playlist' among the user's playlists
            for playlist in user_playlists:
                playlist_list.append(playlist['name'])
                if playlist['name'] == 'voting_playlist':
                    voting_playlist_id = playlist['id']

            if 'voting_playlist' in playlist_list:
                playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{voting_playlist_id}/tracks'

                # Retrieve existing tracks from 'voting_playlist'
                response_delete = requests.get(playlist_tracks_url, headers={'Authorization': f'Bearer {access_token}'})
                tracks_data_delete = response_delete.json().get('items', [])
                track_ids_delete = [track['track']['id'] for track in tracks_data_delete if track.get('track')]

                # Delete existing tracks in 'voting_playlist'
                delete_data = {
                    'tracks': [{'uri': f'spotify:track:{track_id}'} for track_id in track_ids_delete]
                }
                requests.delete(playlist_tracks_url, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, json=delete_data)

                # Add new unique tracks to 'voting_playlist'
                tracks_data_update = response.json().get('items', [])
                track_ids_update = list(set([track['track']['id'] for track in tracks_data_update if track.get('track')]))
                add_data = {
                    'uris': [f'spotify:track:{track_id}' for track_id in track_ids_update]
                }
                requests.post(playlist_tracks_url, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, json=add_data)
                update_cafe_music_model(voting_playlist_id, request.user)

            else:
                tracks_data = response.json().get('items', [])
                track_ids = [track['track']['id'] for track in tracks_data if track.get('track')]

                # Create a new 'voting_playlist' with tracks from the selected playlist
                create_playlist_url = 'https://api.spotify.com/v1/me/playlists'
                data_create = {
                    'name': 'voting_playlist',
                    'description': 'Musics that customers can vote on.'
                }

                response = requests.post(create_playlist_url, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, json=data_create)
                

                if response.status_code == 201:
                    voting_playlist_id = response.json().get('id')

                    # Add tracks to the new 'voting_playlist'
                    add_tracks_url = f'https://api.spotify.com/v1/playlists/{voting_playlist_id}/tracks'
                    unique_track_ids = list(set(track_ids))
                    data_upload = {
                        'uris': [f'spotify:track:{track_id}' for track_id in unique_track_ids]
                    }
                    requests.post(add_tracks_url, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, json=data_upload)
                    update_cafe_music_model(voting_playlist_id, request.user)
                

    # Redirect to the playlist_songs view with the updated voting_playlist_id
    return redirect('playlist_songs', playlist_id=voting_playlist_id)


def update_cafe_music_model(playlist_id, user):
    user_spotify = SpotifyUser.objects.get(user=user)
    access_token = user_spotify.spotify_access_token

    if access_token:
        # Remove existing CafeMusics entries related to the current playlist and user
        CafeMusics.objects.filter(cafe_id=user).delete()

        # Retrieve tracks from the selected playlist
        playlist_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        response = requests.get(playlist_tracks_url, headers={'Authorization': f'Bearer {access_token}'})

        if response.status_code == 200:
            playlist_data = response.json()

            # Loop through each track in the playlist to update CafeMusics
            for track in playlist_data['items']:
                music_name = track['track']['name']
                artists = track['track']['artists']
                # Assuming single artist for simplicity, modify as needed for multiple artists
                artist_name = artists[0]['name']
                spotify_music_id = track['track']['id']
                music_image = track['track']['album']['images'][0]['url']
                music_duration_ms = track['track']['duration_ms']
                
                music_duration_seconds = music_duration_ms // 1000  # Convert to seconds

                # Create or update CafeMusics model instance
                CafeMusics.objects.create(
                    cafe_id=user,
                    music_name=music_name,
                    artist_name=artist_name,
                    music_image=music_image,
                    spotify_music_id=spotify_music_id,
                    music_duration = music_duration_seconds
                )


@login_required(login_url="login")
def display_qr_code(request):
    User = get_user_model()
    user_info = User.objects.get(pk=request.user.pk)  # Retrieve the user info including cafe_name
    cafe_name = user_info.cafe_name
    cafe_id = user_info.pk
    # Get the contact record with the specified pk
    contact = get_object_or_404(get_user_model(), pk=request.user.id)

    # Check if the currently logged-in user is the owner of the contact
    if request.user.id != contact.id:
        return redirect('home')

    # Render the QR code template with the contact object passed as context
    return render(request, 'frontend/qr_code.html', {'contact': contact, 'cafe_name': cafe_name, 'cafe_id': cafe_id})


def music_voting(request, pk):
    cafe = get_object_or_404(get_user_model(), pk=pk)
    musics = CafeMusics.objects.filter(cafe_id=pk)

    user_spotify = SpotifyUser.objects.get(user=pk)
    access_token = user_spotify.spotify_access_token

    if access_token:
        # Fetch the currently playing track
        if musics.count() == 0:
            user_playlists_url = 'https://api.spotify.com/v1/me/playlists'
            playlists_response = requests.get(user_playlists_url, headers={'Authorization': f'Bearer {access_token}'})

            if playlists_response.status_code == 200:
                user_playlists = playlists_response.json().get('items', [])
                voting_playlist_id = None
                playlist_list = []
                
                # Find the 'voting_playlist' among the user's playlists
                for playlist in user_playlists:
                    playlist_list.append(playlist['name'])
                    if playlist['name'] == 'voting_playlist':
                        voting_playlist_id = playlist['id']

                update_cafe_music_model(voting_playlist_id, request.user)

        current_track_url = 'https://api.spotify.com/v1/me/player/currently-playing'
        response = requests.get(current_track_url, headers={'Authorization': f'Bearer {access_token}'})

        if response.status_code == 200:
            current_track = response.json().get('item')
            if current_track:
                current_song_name = current_track['name']
                musics = musics.exclude(music_name=current_song_name)

    if request.method == 'POST':
        cafe_id = request.POST.get('cafe_id')
        for music in musics:
            submit_name = f"submit_{music.id}"
            if submit_name in request.POST:
                music_id = request.POST.get(f"music_id_{music.id}")
                music = get_object_or_404(CafeMusics, pk=music_id)
                music_name = music.music_name
                spotift_music_id = music.spotify_music_id

                customer_ip = request.META.get('REMOTE_ADDR')

                already_voted = cache.get(customer_ip)
                if already_voted:
                    return render(request, 'voting_page.html', {'musics': musics, 'cafe': cafe})
                minute = 60
                cache.set(customer_ip, True, 3 * minute)

                MusicVotes.objects.create(music=music, cafe_id=cafe_id, customer_ip=customer_ip, music_name=music_name, spotift_music_id=spotift_music_id)
                CurrentVotes.objects.create(music=music, cafe_id=cafe_id, customer_ip=customer_ip, music_name=music_name, spotift_music_id=spotift_music_id)

                # Redirect to the same page after voting
                return redirect('music_voting', pk=cafe_id)

    return render(request, 'frontend/voting_page.html', {'musics': musics, 'cafe': cafe})


def spotifyAuth(request):
    # Redirecting to the Spotify authorization page
    spotify_auth_url = 'https://accounts.spotify.com/authorize'
    scopes = [
        'playlist-read-private',
        'playlist-read-collaborative',
        'playlist-modify-public',
        'playlist-modify-private',
        'user-modify-playback-state',
        'user-read-playback-state',
        'user-read-recently-played',
        'user-read-currently-playing',
        'app-remote-control',
        'streaming'
    ]
    scope_string = ' '.join(scopes)
    state = secrets.token_urlsafe(8)
    print(request.user)
    user_spotify, created = SpotifyUser.objects.get_or_create(user=request.user)
    user_spotify.state= state
    user_spotify.save()
    

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': scope_string,
        'state': state
    }
    auth_url = f'{spotify_auth_url}?{urlencode(params)}'
    return redirect(auth_url)


def spotifyCallback(request):
    auth_code = request.GET.get('code')
    print(auth_code)
    auth_state = request.GET.get('state')
    print('state :' + str(auth_state))
    token_url = 'https://accounts.spotify.com/api/token'

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    response = requests.post(token_url, data=data)
    print(response)
    tokens = response.json()
    print(tokens)

    if 'access_token' in tokens and 'refresh_token' in tokens:
        user_info = request.user
        user_spotify, created = SpotifyUser.objects.get_or_create(user=user_info)
        
        if created:
            print(f'New user {user_info.cafe_name} created.')
            user_spotify.spotify_access_token = tokens['access_token']
            user_spotify.spotify_refresh_token = tokens['refresh_token']
            user_spotify.token_expires_at = tokens['expires_in']
            user_spotify.save()

        else:
            print(f'{user_info.cafe_name} updated.')
            user_spotify.spotify_access_token = tokens['access_token']
            user_spotify.spotify_refresh_token = tokens['refresh_token']
            user_spotify.token_expires_at = datetime.now()+ timedelta(seconds=tokens['expires_in'])
            user_spotify.save()

        messages.success(request, 'Successfully connected to Spotify!')
    else:
        messages.error(request, 'Failed to connect to Spotify. Please try again.')

    return redirect('home')



