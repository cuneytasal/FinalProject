import django
django.setup()
from datetime import datetime, timedelta
import requests
from django.core.management.base import BaseCommand
from frontend.credentials import CLIENT_SECRET, CLIENT_ID
from frontend.models import SpotifyUser
import pytz



class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        users = SpotifyUser.objects.all()
        token_url = 'https://accounts.spotify.com/api/token'
        utc = pytz.UTC

        for user in users:
            expiration_date = user.token_expires_at.replace(tzinfo=utc)
            today = datetime.now().replace(tzinfo=utc)
            #print(expiration_date)
            #print(today)
            if today >= expiration_date - timedelta(minutes=40):
                    payload = {
                        'grant_type': 'refresh_token',
                        'refresh_token': user.spotify_refresh_token,
                        'client_id': CLIENT_ID,
                        'client_secret': CLIENT_SECRET
                    }

                    response = requests.post(token_url, data=payload)

                    if response.status_code == 200:
                        data = response.json()
                        user.spotify_access_token = data['access_token']
                        expires_in = data['expires_in']
                        user.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        user.save()
                        print('Access token succesfully refreshed:', response.text)

                    else:
                        print('Failed to refresh access token:', response.text)
            else:
                print('There is no need to refresh right now:')