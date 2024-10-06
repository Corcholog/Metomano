"use client";

import { useState } from 'react';
import CensoredLyricsCard from './components/CensoredLyricsCard/CensoredLyricsCard';

export default function Home() {
  const [artist, setArtist] = useState('');
  const [songs, setSongs] = useState([]);
  const [censoredLyrics, setCensoredLyrics] = useState('');
  const [censorship, setCensorship] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [songName, setSongName] = useState('');
  const [userInputs, setUserInputs] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [showCensorship, setShowCensorship] = useState(false);
  const [score, setScore] = useState(null);
  const [results, setResults] = useState([]);
  const [showEmbed, setShowEmbed] = useState(false);
  const [spotifyEmbedUrl, setSpotifyEmbedUrl] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setShowCensorship(false);
    setScore(null);
    setResults([]);
    setSpotifyEmbedUrl('');

    try {
      const response = await fetch(`http://localhost:8000/songs?artist=${artist}&lang=ES`);
      if (!response.ok) {
        throw new Error('Error al obtener las canciones');
      }

      const data = await response.json();
      setSongs(data.songs);

      const songPoolResponse = await fetch('http://localhost:8000/song_pool', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ songs: data.songs, N: 5 }),
      });

      if (!songPoolResponse.ok) {
        throw new Error('Error al filtrar las canciones');
      }

      const songPoolData = await songPoolResponse.json();
      const filteredSongs = songPoolData.selected_songs;

      const lyricsResponse = await fetch('http://localhost:8000/get_lyrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ songs: filteredSongs }),
      });

      if (!lyricsResponse.ok) {
        throw new Error('Error al obtener las letras censuradas');
      }

      const lyricsData = await lyricsResponse.json();
      const firstSong = filteredSongs[0];
      setCensoredLyrics(lyricsData[firstSong.name].censored_lyrics);
      setCensorship(lyricsData[firstSong.name].censorship);
      setSongName(firstSong.name);

      const trackId = firstSong.external_urls.split('track/')[1];
      setSpotifyEmbedUrl(`https://open.spotify.com/embed/track/${trackId}?utm_source=generator`);

      setUserInputs([]);
      setCurrentInput('');
      setShowEmbed(false);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputSubmit = (e) => {
    e.preventDefault();
    setUserInputs([...userInputs, currentInput]);
    setCurrentInput('');
  };

  const calculateScore = async () => {
    try {
      const response = await fetch('http://localhost:8000/get_score', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_input: userInputs,
          user_answers: userInputs,
          censorship: censorship,
          answers: censorship,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al calcular el puntaje');
      }

      const scoreData = await response.json();
      setScore(scoreData.score);

      const resultData = censorship.map((correctWord, index) => ({
        userWord: userInputs[index] || '',
        correctWord,
        isCorrect: (userInputs[index] || '').toLowerCase() === correctWord.toLowerCase(),
      }));
      setResults(resultData);
      setShowEmbed(true);
      setShowCensorship(true);
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className="min-h-screen p-8 pb-20 grid grid-cols-1 sm:grid-cols-2 gap-16 items-center justify-center font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 items-center sm:items-start w-full max-w-sm mx-auto">
        <h1 className="text-2xl font-bold text-center">Ingresa un artista para jugar</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 items-center w-80">
          <input
            type="text"
            value={artist}
            onChange={(e) => setArtist(e.target.value)}
            placeholder="Ingresa el nombre del artista"
            className="border p-2 rounded text-black w-full"
            required
          />
          <button type="submit" className="bg-green-600 text-white rounded px-4 py-2 w-full">
            Buscar
          </button>
        </form>

        {loading && <p>Buscando canciones...</p>}
        {error && <p className="text-red-500">{error}</p>}

        {censoredLyrics && (
          <div className="w-80">
            <CensoredLyricsCard song_name={songName} censoredLyrics={censoredLyrics} />
            <form onSubmit={handleInputSubmit} className="mt-4">
              <input
                type="text"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                placeholder="Ingresa la palabra censurada"
                className="border p-2 rounded text-black w-full"
              />
              <button type="submit" className="bg-blue-600 text-white rounded px-4 py-2 w-full mt-2">
                Ingresar
              </button>
            </form>
            <button onClick={calculateScore} className="bg-green-600 text-white rounded px-4 py-2 w-full mt-4">
              Enviar Respuestas
            </button>
          </div>
        )}
      </main>

      <aside className="flex flex-col gap-4 w-full">
        {showEmbed && (
          <iframe
            style={{ borderRadius: '12px' }}
            src={spotifyEmbedUrl}
            width="100%"
            height="352"
            frameBorder="0"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
          ></iframe>
        )}
        {score !== null && (
          <>
            <p className="text-xl font-bold">Tu puntaje: {score}</p>
            <ul className="mt-4 flex flex-col gap-2">
              {results.map((result, index) => (
                <li key={index} className="flex items-center gap-4">
                  <span>{result.userWord}</span>
                  <span>→ {result.correctWord}</span>
                  {result.isCorrect ? (
                    <span className="text-green-600 font-bold">✓</span>
                  ) : (
                    <span className="text-red-600 font-bold">✗</span>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
      </aside>
    </div>
  );
}
