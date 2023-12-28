from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerUser, name='register'),
    path('home/', views.home, name='home'),
    path('playlist/<str:playlist_id>/', views.playlist_songs, name='playlist_songs'),
    path('start_playback/<str:access_token>/<str:playlist_id>/', views.start_playback, name='start_playback'),
    path('stats/<str:playlist_id>/', views.cafe_songs_stats, name='cafe_songs_stats'),
    path('spotify-auth/', views.spotifyAuth, name='spotify_auth'),
    path('spotify-callback/', views.spotifyCallback, name='spotify_callback'),
    path('copy-playlist/<str:playlist_id>/', views.copy_playlist_and_rename, name='copy_playlist_and_rename'),
    path('cafe/<int:pk>/vote/', views.music_voting, name='music_voting'),
    path('search/<int:pk>/vote/', views.searchBar, name='search'),
    path('qr_code/<str:playlist_id>/', views.display_qr_code, name='display_qr_code'),
    path('about/<str:playlist_id>/', views.about, name='about')
]
