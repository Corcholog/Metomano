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

load_dotenv()

dbname = os.getenv("PG_DB")
user = os.getenv("PG_USER")
password = os.getenv("PG_PASS")
host = os.getenv("PG_HOST")

genius_access_token = os.getenv("GENIUS_ACCESS")
genius = Genius(genius_access_token, remove_section_headers=True, verbose=False, retries=5)
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

token = sp.get_token(client_id, client_secret)

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

@app.put("/update_all_lyrics")
async def update_all_lyrics():
    cursor = conn.cursor()
    
    # Obtener todas las canciones con sus nombres, IDs y nombres de artistas
    query = """
    SELECT Track.id, Track.name, Artist.name 
    FROM Track 
    JOIN Track_Artist ON Track.id = Track_Artist.track_id 
    JOIN Artist ON Track_Artist.artist_id = Artist.id
    """
    cursor.execute(query)
    tracks = cursor.fetchall()
    
    updated_tracks = []
    
    for track_id, track_name, artist_name in tracks:
        # Obtener la letra limpia usando el nombre del artista en get_lyrics
        clean_lyrics = ly.get_lyrics(track_name, artist_name, genius)
        
        if clean_lyrics:
            # Actualizar la letra en la base de datos
            update_query = "UPDATE Track SET lyrics = %s WHERE id = %s"
            cursor.execute(update_query, (clean_lyrics, track_id))
            conn.commit()  # Commit después de cada actualización

            updated_tracks.append(track_id)
            print(f"Letra actualizada para {track_name} de {artist_name} (ID: {track_id})")

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
        
        censored_lyrics, censorship = cs.censurar(chosen_section, LANG=song.lang, percentage=0.5)
        
        # Agregar al mapa
        result_map[song_name] = {
            "censored_lyrics": censored_lyrics,
            "censorship": censorship
        }
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
        artist_id = sp.get_artist_id(token, artist, client_id, client_secret)
        # Verifica si el artista está en la base de datos; si no, lo obtiene de Spotify
        artist_name_query = "SELECT name FROM Artist WHERE id = %s"
        cursor.execute(artist_name_query, (artist_id,))
        artist_name = cursor.fetchone()
        new_artist = False
        if artist_name is None:
            new_artist = True
            artist_name = sp.get_artist_name(token, artist_id)
            # Inserta el artista en la base de datos
            cursor.execute("INSERT INTO Artist (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", (artist_id, artist_name))
            conn.commit()  # Commit para asegurar la inserción del artista
        else:
            artist_name = artist_name[0]

        # Consulta las canciones del artista en la base de datos
        tracks_query = """
        SELECT t.id, t.name, t.lyrics, t.lang, t.external_urls
        FROM Track t
        JOIN Track_Artist ta ON t.id = ta.track_id
        WHERE ta.artist_id = %s
        """
        cursor.execute(tracks_query, (artist_id,))
        tracks = cursor.fetchall()

        # Si no hay canciones en la base de datos, consulta la API de Spotify
        if not tracks:
            print("No songs found in database, calling Spotify API...")
            tracks_from_spotify = sp.get_all_tracks_by_artist(token, artist_id, artist_name)

            # Inserta cada canción y sus artistas en la base de datos
            for track in tracks_from_spotify:
                # Inserta el álbum en la tabla Album si aún no existe
                album_id = track['album_id']
                album_name = track['album_name']

                cursor.execute("SELECT id FROM Album WHERE id = %s", (album_id,))
                album_exists = cursor.fetchone()
                
                if not album_exists:
                    insert_album_query = """
                    INSERT INTO Album (id, artist_id, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """
                    cursor.execute(insert_album_query, (album_id, artist_id, album_name))
                    conn.commit()  # Commit para asegurar la inserción del álbum
        
                external_url = track.get('external_urls', {}).get('spotify', '')
                insert_track_query = """
                INSERT INTO Track (id, album_id, name, lyrics, lang, external_urls)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """
                track_data = (
                    track['id'],
                    track['album_id'],
                    track['name'],
                    track.get('lyrics', None),
                    track.get('lang', lang) if not track.get('lang') else track.get('lang'),
                    external_url
                )
                cursor.execute(insert_track_query, track_data)
                conn.commit()  # Commit para asegurar la inserción de la canción
                
                for artist in track['artists']:
                    artist_name = artist['name']  # Extrae solo el nombre del artista
                    artist_id_for_track = artist['id']  # Extrae el ID del artista
                    cursor.execute("SELECT id FROM Artist WHERE id = %s", (artist_id_for_track,))
                    artist_record = cursor.fetchone()
                    
                    if not artist_record:
                        insert_artist_query = "INSERT INTO Artist (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING"
                        cursor.execute(insert_artist_query, (artist_id_for_track, artist_name))
                        conn.commit()  # Commit para asegurar la inserción del artista
                    
                    insert_track_artist_query = """
                    INSERT INTO Track_Artist (track_id, artist_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                    """
                    cursor.execute(insert_track_artist_query, (track['id'], artist_id_for_track))
                    conn.commit()  # Commit para asegurar la inserción en la tabla intermedia

            # Reejecuta la consulta para obtener las canciones insertadas desde la base de datos
            cursor.execute(tracks_query, (artist_id,))
            tracks = cursor.fetchall()

        # Obtiene las letras faltantes y actualiza la base de datos
       
        updated_tracks = []
        for track in tracks:
            track_id, track_name, lyrics, track_lang, external_urls = track

            if new_artist and ((lyrics is None) or (lyrics == '')):
                lyrics = ly.get_lyrics(track_name, artist_name, genius)

                if lyrics:
                    update_lyrics_query = "UPDATE Track SET lyrics = %s WHERE id = %s"
                    cursor.execute(update_lyrics_query, (lyrics, track_id))
                    conn.commit()  # Commit para asegurar la inserción de las letras
            
            if not track_lang:
                update_lang_query = "UPDATE Track SET lang = %s WHERE id = %s"
                cursor.execute(update_lang_query, (lang, track_id))
                conn.commit()  # Commit para asegurar la actualización del idioma
                track_lang = lang

            updated_tracks.append({
                "id": track_id,
                "name": track_name,
                "lyrics": lyrics,
                "lang": track_lang,
                "external_urls": external_urls
            })
        elapsed_time = time.time() - start_time
        print(f"La consulta tardó {elapsed_time:.2f} segundos")
        return {"songs": updated_tracks}

    finally:
        cursor.close()
