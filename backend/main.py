import logging
import random
from fastapi import FastAPI, HTTPException, Query
import psycopg2
import os
from dotenv import load_dotenv
from lyricsgenius import Genius
import spoti as sp
import lyrics as ly 
import censorship as cs
import scoresys as sc
import time
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import DictCursor
from models.models import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Desactivar mensajes de depuración para `urllib3` y `requests`
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
load_dotenv()

dbname = os.getenv("PG_DB")
user = os.getenv("PG_USER")
password = os.getenv("PG_PASS")
host = os.getenv("PG_HOST")
sp_dc = os.getenv("SP_DC")
sp_key = os.getenv("SP_KEY")

genius_access_token = os.getenv("GENIUS_ACCESS")
genius = Genius(genius_access_token, remove_section_headers=True, verbose=False, retries=5)
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

token = sp.get_token(client_id, client_secret)

spotify_lyrics = ly.SpotifyLyrics(sp_dc, sp_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a PostgreSQL
try:
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host
    )
except psycopg2.OperationalError as e:
    print("Error al conectar a la base de datos:", e)
    raise

@app.put("/update_popularity")
async def update_popularity():
    cursor = conn.cursor()

    # Obtener todas las canciones con sus IDs
    query = """
    SELECT id 
    FROM Track
    """
    cursor.execute(query)
    tracks = cursor.fetchall()

    updated_tracks = []

    for track_id in tracks:
        track_spotify_id = track_id[0]  # El identificador es directamente el ID de la canción en Spotify

        # Obtener la popularidad desde la API de Spotify
        popularity = sp.get_track_popularity(track_spotify_id, token)

        if popularity is not None:
            # Actualizar la popularidad en la base de datos
            update_query = "UPDATE Track SET popularidad = %s WHERE id = %s"
            cursor.execute(update_query, (popularity, track_spotify_id))
            conn.commit()
            updated_tracks.append(track_spotify_id)

    cursor.close()
    return {"updated_tracks": updated_tracks, "message": "Actualización de popularidad completada"}

@app.put("/update_lyrics_by_artist")
async def update_lyrics_by_artist(artist_name: str = Query(..., description="Nombre del artista a actualizar")):
    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        # Obtener el ID del artista a partir del nombre
        artist_id = sp.get_artist_id(token, artist_name, client_id, client_secret)
        if not artist_id:
            return {"status": False, "message": f"No se encontró el artista: {artist_name}"}

        # Obtener las canciones del artista en la base de datos
        query = """
        SELECT t.id, t.name, t.lyrics
        FROM Track t
        JOIN Track_Artist ta ON t.id = ta.track_id
        WHERE ta.artist_id = %s
        """
        cursor.execute(query, (artist_id,))
        tracks = cursor.fetchall()

        if not tracks:
            return {"status": False, "message": f"No se encontraron canciones para el artista: {artist_name}"}

        updated_tracks = []

        # Actualizar las letras de las canciones
        for track_id, track_name, existing_lyrics in tracks:
            try:
                # Obtener la letra de la canción
                new_lyrics = spotify_lyrics.getLyricsMM(track_id, track_name)

                if new_lyrics and new_lyrics != existing_lyrics:
                    # Actualizar la letra en la base de datos
                    update_query = "UPDATE Track SET lyrics = %s WHERE id = %s"
                    cursor.execute(update_query, (new_lyrics, track_id))
                    conn.commit()
                    updated_tracks.append(track_name)

            except Exception as e:
                print(f"Error al obtener o actualizar letras para {track_name}: {e}")
                continue

        if updated_tracks:
            return {"status": True, "updated_tracks": updated_tracks, "message": f"Letras actualizadas para el artista {artist_name}"}
        else:
            return {"status": True, "message": f"No había letras nuevas que actualizar para el artista {artist_name}"}

    except Exception as e:
        print(f"Error al actualizar letras para el artista {artist_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar letras: {e}")

    finally:
        cursor.close()


@app.put("/update_all_lyrics")
async def update_all_lyrics():
    cursor = conn.cursor()

    # Obtener todas las canciones con sus nombres, IDs y nombres de artistas
    query = """
    SELECT id, name, lyrics
    FROM Track;

    """
    cursor.execute(query)
    tracks = cursor.fetchall()

    updated_tracks = []

    for track_id, track_name, existing_lyrics in tracks:
        try:
            clean_lyrics = spotify_lyrics.getLyricsMM(track_id, track_name)
            

            # Solo actualizar si hay letras nuevas y son diferentes a las existentes
            if clean_lyrics and existing_lyrics != clean_lyrics:
                # Actualizar la letra en la base de datos
                update_query = "UPDATE Track SET lyrics = %s WHERE id = %s"
                cursor.execute(update_query, (clean_lyrics, track_id))
                conn.commit()  # Commit después de cada actualización

                updated_tracks.append(track_id)


        except Exception as e:
            print(f"Error al obtener o actualizar letras para {track_name}: {e}")
            continue

    cursor.close()
    return {"updated_tracks": updated_tracks, "message": "Actualización de letras completada"}


@app.post("/song_pool")
async def song_pool(request: SongPoolRequest):
    # Variable booleana para decidir si se mezclan las canciones
    shuffle_songs = True
    
    # esto deberia hacerlo con una query
    # Filtra las canciones para asegurar que tengan letras
    songs_with_lyrics = [song for song in request.songs if song.lyrics]
    N = request.N

    if shuffle_songs:
        random.shuffle(songs_with_lyrics)
    
    # Verifica si N es mayor que la cantidad de canciones con letras disponibles
    if N > len(songs_with_lyrics):
        selected_songs = songs_with_lyrics
    else:
        # Selecciona las primeras N canciones que tengan letras
        selected_songs = songs_with_lyrics[:N]
    

    
    return {"selected_songs": selected_songs}

@app.post("/get_score")
async def get_score(request: ScoreRequest):
    total_score = sc.get_score(request.user_input, request.user_answers, request.censorship, request.answers)
    return {"score": total_score}

@app.post("/get_lyrics")
async def get_lyrics(request: LyricsRequest):
    start_time = time.time()
    songs = request.songs
    result_map = {}

    for song in songs:
        lyrics = song.lyrics  # Usa la notación de punto para acceder a los atributos
        song_name = song.name  # Usa la notación de punto para acceder a los atributos

        if not lyrics:
            continue
        
        sections = ly.dividir_por_secciones(lyrics)
        idx = random.randint(0, len(sections) - 1)
        chosen_section = sections[idx]
        
        # Reintentar hasta que se obtenga una sección con más de dos líneas
        while len(chosen_section.split("\n")) <= 2:
            idx = random.randint(0, len(sections) - 1)
            chosen_section = sections[idx]
        
        # Dividir la sección en líneas individuales
        lines = chosen_section.split("\n")
        
        # Si la sección tiene más de 6 líneas, selecciona entre 4, 5 o 6 líneas consecutivas
        if len(lines) > 6:
            num_lines = random.choice([4, 5, 6])  # Elegir aleatoriamente cuántas líneas tomar
            start_idx = random.randint(0, len(lines) - num_lines)  # Elegir el índice de inicio
            chosen_section = "\n".join(lines[start_idx:start_idx + num_lines])  # Obtener el subconjunto de líneas
        
        # Censurar las líneas seleccionadas
        censored_lyrics, censorship = cs.censurar(chosen_section, LANG=song.lang, debug=True,porcentaje_censura=0.3)
        
        # Agregar al mapa
        result_map[song_name] = {
            "censored_lyrics": censored_lyrics,
            "censorship": censorship
        }
        break

    elapsed_time = time.time() - start_time
    print(f"La censura tardó {elapsed_time:.2f} segundos")
    return result_map


@app.post("/get_questions")
async def get_questions(request: QuestionRequest):
    
    return

@app.get("/songs")
async def get_songs(lang: str = Query(..., description="El idioma"),
                    artist: str = Query(..., description="El nombre del artista", min_length=1) ):
    start_time = time.time()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Obtener el ID del artista desde la API de Spotify
        artist_id = sp.get_artist_id(token, artist, client_id, client_secret)
        
        # Verificar si el artista ya está en la base de datos
        artist_name_query = "SELECT name FROM Artist WHERE id = %s"
        cursor.execute(artist_name_query, (artist_id,))
        artist_name = cursor.fetchone()
        new_artist = False
        
        if artist_name is None:
            # Si el artista no está en la base de datos, se obtiene de Spotify y se inserta
            new_artist = True
            artist_name = sp.get_artist_name(token, artist_id)
            cursor.execute("INSERT INTO Artist (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", 
                           (artist_id, artist_name))
            conn.commit()
        else:
            artist_name = artist_name[0]

        # Consulta las canciones del artista en la base de datos
        tracks_query = """
        SELECT t.id, t.name, t.lyrics, t.lang, t.external_urls, t.popularidad
        FROM Track t
        JOIN Track_Artist ta ON t.id = ta.track_id
        WHERE ta.artist_id = %s
        ORDER BY t.popularidad DESC
        """
        cursor.execute(tracks_query, (artist_id,))
        tracks = cursor.fetchall()

        # Si no hay canciones en la base de datos, consulta la API de Spotify
        if not tracks:
            print("No songs found in database, calling Spotify API...")
            tracks_from_spotify = sp.get_all_tracks_by_artist(token, artist_id, artist_name)

            # Inserta cada canción y sus artistas en la base de datos
            for track in tracks_from_spotify:
                album_id = track['album_id']
                album_name = track['album_name']

                # Verificar si el álbum ya existe, si no, insertarlo
                cursor.execute("SELECT id FROM Album WHERE id = %s", (album_id,))
                album_exists = cursor.fetchone()

                if not album_exists:
                    insert_album_query = """
                    INSERT INTO Album (id, artist_id, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """
                    cursor.execute(insert_album_query, (album_id, artist_id, album_name))
                    conn.commit()

                external_url = track.get('external_urls', {}).get('spotify', '')

                # Obtener la popularidad de la canción desde la API de Spotify
                popularity = sp.get_track_popularity(track['id'], token)

                # Obtener letras antes de la inserción
                lyrics = spotify_lyrics.getLyricsMM(track['id'], track['name'])

                # Inserta la canción en la tabla Track, incluyendo la letra (si está disponible)
                insert_track_query = """
                INSERT INTO Track (id, album_id, name, lyrics, lang, external_urls, popularidad)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """
                track_data = (
                    track['id'],
                    track['album_id'],
                    track['name'],
                    lyrics,  # Se inserta la letra obtenida (si está disponible)
                    track.get('lang', lang) if not track.get('lang') else track.get('lang'),
                    external_url,
                    popularity
                )
                cursor.execute(insert_track_query, track_data)
                conn.commit()

                 # Inserta solo el artista actual (obtenido por parámetro) en la tabla intermedia
                insert_track_artist_query = """
                INSERT INTO Track_Artist (track_id, artist_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
                """
                cursor.execute(insert_track_artist_query, (track['id'], artist_id))
                conn.commit()

                

            # Reejecutar la consulta para obtener las canciones insertadas desde la base de datos
            cursor.execute(tracks_query, (artist_id,))
            tracks = cursor.fetchall()

        # Obtiene las letras faltantes y actualiza la base de datos
        updated_tracks = []

        for track in tracks:
            track_id, track_name, lyrics, track_lang, external_urls, popularidad = track

            # Si no hay letras en la base de datos, intenta obtenerlas y actualizarlas
            if new_artist and not lyrics:
                lyrics = spotify_lyrics.getLyricsMM(track_id, track_name)
                print(lyrics)
                if lyrics:
                    update_lyrics_query = "UPDATE Track SET lyrics = %s WHERE id = %s"
                    cursor.execute(update_lyrics_query, (lyrics, track_id))
                    conn.commit()

            # Si no hay idioma, actualizarlo
            if not track_lang:
                update_lang_query = "UPDATE Track SET lang = %s WHERE id = %s"
                cursor.execute(update_lang_query, (lang, track_id))
                conn.commit()
                track_lang = lang

            updated_tracks.append({
                "id": track_id,
                "name": track_name,
                "lyrics": lyrics,
                "lang": track_lang,
                "external_urls": external_urls,
                "popularidad": popularidad
            })

        elapsed_time = time.time() - start_time
        print(f"La consulta tardó {elapsed_time:.2f} segundos")
        return {"songs": updated_tracks}

    finally:
        cursor.close()