"use client";

export function GameLoop({ songs }){

    return (
        <div className="song-list">
          <ul>
            {songs.map((song) => (
              <li key={song.id} className="song-item">
                {song.name}
              </li>
            ))}
          </ul>
        </div>
      );
}