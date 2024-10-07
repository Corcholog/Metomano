import re
import time
import spotify_lyrics_scraper as spotify
def get_lyrics(song, artist, genius):
    response = genius.search_song(song, artist)
    if response:
        return clean_lyrics(response.lyrics)
    return None

def clean_lyrics(lyrics):
    if lyrics:
        lyrics = re.sub(r'^.*?Lyrics', 'Lyrics', lyrics, flags=re.DOTALL)
        lyrics = re.sub(r"See .* LiveGet tickets as low as \$\d+\n?", "\n", lyrics)
        lyrics = re.sub(r"\d+Embed", "", lyrics)

        #lyrics = lyrics.splitlines()[1:]  # Divide en líneas y elimina la primera, que contiene lyrics
        #lyrics = "\n".join(lyrics)  # Vuelve a unir el texto con saltos de línea
        # Ahora, eliminamos la primera línea (que podría ser vacía o no)
        lyrics = lyrics.split("\n", 1)[1]  # Divide en 2 partes, manteniendo todo excepto la primera línea

        # Preservar líneas vacías
        lyrics = "\n".join(lyrics.split("\n"))
        keywords = ['Translations', 'Embed', 'You might also like']
        for keyword in keywords:
            lyrics = lyrics.replace(keyword, '')
    return lyrics

def dividir_por_secciones(lyrics):
    # Dividimos la letra en secciones usando líneas vacías como separadores
    secciones = lyrics.split("\n\n")  # Cada línea vacía separa una sección
    return secciones

class SpotifyLyrics:
    def __init__(self, sp_dc, sp_key):
        self.sp_dc = sp_dc
        self.sp_key = sp_key
        self.token_info = self.get_new_token()  # Obtener el token una vez al inicializar

    def get_new_token(self):
        """
        Obtiene un nuevo token de Spotify.
        """
        return spotify.getToken(self.sp_dc, self.sp_key)

    def getLyricsMM(self, track_id=None, song_name=None):
        """
        Obtiene la letra completa de una canción utilizando la API de Spotify,
        reemplazando las líneas que contienen el carácter "♪" por una línea vacía.
        Si no se encuentra la letra, retorna un string vacío.

        :param track_id: ID de la pista de Spotify (opcional)
        :param song_name: Nombre de la canción (opcional)
        :return: Letra completa de la canción como un string o un string vacío si no se encuentra.
        """
        try:
            # Obtener el token que ya fue generado una vez
            token = self.token_info  # Utiliza el token ya generado

            # Obtener las letras de la canción
            lyrics = spotify.getLyrics(token, trackId=track_id, songName=song_name)


            # Verificar que las letras se obtuvieron correctamente
            if isinstance(lyrics, spotify.spotifyDict):
                # Formatear las letras para obtener solo el contenido
                formatted_lyrics = lyrics.formatLyrics(mode=0)  # El modo 0 es solo las letras

                # Verificar que 'message' es una lista con las líneas de la letra
                if isinstance(formatted_lyrics['message'], list):
                    # Reemplazar las líneas que contienen "♪" por una línea vacía
                    replaced_lyrics = [line if "♪" not in line else "" for line in formatted_lyrics['message']]

                    # Combinar las líneas en un solo string
                    full_lyrics = "\n".join(replaced_lyrics)
                    return full_lyrics
                else:
                    return ""  # Retorna un string vacío si el formato no es el esperado.
            else:
                print(f"Lyrics response is not a spotifyDict: {lyrics}")
                return ""  # Retorna un string vacío si no se encuentran las letras.

        except Exception as e:
            print(f"Error al obtener las letras: {e}")
            return ""  # Retorna un string vacío en caso de cualquier error inesperado.