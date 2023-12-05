from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerUser, name='register'),
    path('home/', views.home, name='home'),
    path('playlist/<str:playlist_id>/', views.playlist_songs, name='playlist_songs'),
    path('spotify-auth/', views.spotifyAuth, name='spotify_auth'),
    path('spotify-callback/', views.spotifyCallback, name='spotify_callback'),
    path('copy-playlist/<str:playlist_id>/', views.copy_playlist_and_rename, name='copy_playlist_and_rename'),
    path('cafe/<int:pk>/vote/', views.music_voting, name='music_voting'),
    path('qr_code/', views.display_qr_code, name='display_qr_code'),
]
