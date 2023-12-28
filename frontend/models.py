from django.db import models
from django.contrib.auth import get_user_model
from .credentials import REDIRECT_URI, CLIENT_SECRET, CLIENT_ID
import requests
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class SpotifyUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spotify_access_token = models.CharField(max_length=500)
    spotify_refresh_token = models.CharField(max_length=500)
    state = models.CharField(max_length=500, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)  # Added token expiration field
    
    def __str__(self) -> str:
        return super().__str__()


class CafeMusics(models.Model):
    cafe_id = models.ForeignKey(User, on_delete=models.CASCADE)
    music_name = models.CharField(max_length=100)
    artist_name = models.CharField(max_length=100)
    music_image = models.URLField(max_length=500)
    spotify_music_id = models.CharField(max_length=500, null=True)
    music_duration = models.PositiveIntegerField(null=True)


class MusicVotes(models.Model):
    music = models.ForeignKey(CafeMusics, on_delete=models.CASCADE)
    music_name = models.CharField(max_length=100, null=True)
    cafe = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_ip = models.GenericIPAddressField()
    spotify_music_id = models.CharField(max_length=500, null=True)
    vote_date = models.DateTimeField(default=timezone.now)

   
class CurrentVotes(models.Model):
    music = models.ForeignKey(CafeMusics, on_delete=models.CASCADE)
    music_name = models.CharField(max_length=100, null=True)
    cafe = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_ip = models.GenericIPAddressField()
    spotify_music_id = models.CharField(max_length=500, null=True)
    vote_date = models.DateTimeField(default=timezone.now)