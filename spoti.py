from requests import post, get
import base64
def get_token(client_id, client_secret):
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    url = "https://accounts.spotify.com/api/token"  # URL corregida
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)

    # Cambia a usar .json() para analizar directamente la respuesta como JSON
    json_result = result.json()
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def get_playlist_items(token, playlist_id="3pS3eTdTR9s086EZ8XkZyO", limit=10, offset=0):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit={limit}&offset={offset}"
    headers = get_auth_header(token)
    result = get(url=url, headers=headers)
    
    result.raise_for_status()  # Lanza un error en caso de una respuesta HTTP de error
    json_result = result.json()
    return json_result

def print_playlist_items(playlist_json):
    # Acceder a la lista de canciones
    items = playlist_json.get('items', [])
    
    for item in items:
        track = item.get('track', {})
        # Extraer detalles de cada canción
        song_name = track.get('name')
        artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
        album = track.get('album', {}).get('name')
        duration_ms = track.get('duration_ms')

        # Información adicional
        song_id = track.get('id')
        explicit = track.get('explicit')
        popularity = track.get('popularity')
        track_number = track.get('track_number')
        available_markets = track.get('available_markets', [])

        # Convertir duración de milisegundos a minutos y segundos
        duration_min = duration_ms // 60000
        duration_sec = (duration_ms % 60000) // 1000

        print(f"Song ID: {song_id}")
        print(f"Song: {song_name}")
        print(f"Artist: {artists}")
        print(f"Album: {album}")
        print(f"Length: {duration_min}:{duration_sec:02d}")
        print(f"Explicit: {explicit}")
        print(f"Popularity: {popularity}")
        print(f"Track Number: {track_number}")
        print(f"Available Markets: {', '.join(available_markets[:5])}...")  # Mostrar solo los primeros 5 mercados
        print("-" * 40)

def get_artist_id(artist):
    # debo obtener el ID del artista buscando el artista con web scraping...
    return None

def get_tracks(artist_id):
    ### no hay metodo directo, debo obtener todos los tracks de todos los albums
    return None

def get_artist_albums(token, artist_id, limit=20, offset=0, sort = True):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = get_auth_header(token)
    params = {
        "limit": limit,
        "offset": offset,
        "include_groups": "album",  # Asegúrate de que solo se incluyan álbumes
    }
    result = get(url=url, headers=headers, params=params)
    
    result.raise_for_status()  # Lanza un error en caso de una respuesta HTTP de error
    json_result = result.json()
    
    items = json_result.get('items', [])
    sorted_albums = sorted(items, key=lambda album: album['release_date'], reverse=True)
    return sorted_albums if sort else items

def get_top_tracks(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = get_auth_header(token)
    result = get(url=url, headers=headers)
    
    result.raise_for_status()  # Lanza un error en caso de una respuesta HTTP de error
    json_result = result.json()
    tracks = json_result.get('tracks', [])
    # Crea un diccionario con el nombre de la cancion de clave y de value el objeto completo
    top_tracks = {track['name']: track for track in tracks}
    return top_tracks

def get_album_tracks(token, album_id, artist_name=None):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = get_auth_header(token)
    result = get(url=url, headers=headers)
    
    result.raise_for_status()
    json_result = result.json()
    
    tracks = json_result.get('items', [])
    
    # Añadimos el nombre del artista a cada pista, si está disponible
    for track in tracks:
        track['artist_name'] = artist_name
    
    return tracks

def get_artist_id(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    params = {
        'q': artist_name,
        'type': 'artist',
        'limit': 1  # Devolver solo el primer resultado más relevante
    }
    
    result = get(url, headers=headers, params=params)
    
    result.raise_for_status()  # Lanza un error en caso de que la respuesta HTTP sea un error
    json_result = result.json()
    
    artists = json_result.get('artists', {}).get('items', [])
    if not artists:
        print(f"No se encontró ningún artista con el nombre '{artist_name}'")
        return None
    
    # Obtenemos el ID del primer artista encontrado
    artist_id = artists[0]['id']
    return artist_id

def get_artist_name(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(token)
    result = get(url=url, headers=headers)
    
    result.raise_for_status()
    json_result = result.json()
    artist_name = json_result.get('name', 'Unknown Artist')
    return artist_name

def get_all_tracks_by_artist(token, artist_id):
    # Obtener el nombre del artista
    artist_name = get_artist_name(token, artist_id)
    
    # Obtener los álbumes del artista
    albums = get_artist_albums(token, artist_id)
    all_tracks = []
    
    for album in albums:
        album_id = album['id']
        # Pasar el nombre del artista a get_album_tracks
        tracks = get_album_tracks(token, album_id, artist_name=artist_name)
        
        for track in tracks:
            # Obtener más detalles del track, incluyendo popularidad
            track_id = track['id']
            track_details = get(f"https://api.spotify.com/v1/tracks/{track_id}", headers=get_auth_header(token)).json()
            
            # Añadir el nombre del artista al track
            track_details['artist_name'] = artist_name
            
            all_tracks.append(track_details)

    # Ordenar por popularidad
    all_tracks_sorted = sorted(all_tracks, key=lambda x: x.get('popularity', 0), reverse=True)
    
    return all_tracks_sorted

def get_playlist_tracks_with_artists(token, playlist_id, limit=100):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)
    params = {
        'limit': limit  # El máximo permitido por Spotify es 100 por solicitud
    }
    
    result = get(url, headers=headers, params=params)
    result.raise_for_status()  # Lanza un error en caso de una respuesta HTTP de error
    json_result = result.json()
    
    tracks = []
    for item in json_result.get('items', []):
        track = item.get('track', {})
        if track is None:  # A veces el track puede ser None
            continue

        song_name = track.get('name', 'Unknown Song')
        artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
        
        tracks.append({
            'name': song_name,  # Aquí se usa 'name' en lugar de 'song_name'
            'artist_name': artists  # Mantener 'artist_name' para el artista
        })
    
    return tracks