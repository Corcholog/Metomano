from fastapi import FastAPI, HTTPException
import psycopg2
import os
from dotenv import load_dotenv
from lyricsgenius import Genius
import spoti as sp
import lyrics as ly  # Supongamos que tienes una función para obtener letras
import time

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

@app.get("/songs/{artist_id}/{lang}")
async def get_songs(artist_id: str, lang: str):
    start_time = time.time()
    cursor = conn.cursor()

    try:
        # Verifica si el artista está en la base de datos; si no, lo obtiene de Spotify
        artist_name_query = "SELECT name FROM Artist WHERE id = %s"
        cursor.execute(artist_name_query, (artist_id,))
        artist_name = cursor.fetchone()

        if artist_name is None:
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

            if lyrics is None or lyrics == '':
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
