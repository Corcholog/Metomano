import React from 'react';

const CensoredLyricsCard = ({ song_name, censoredLyrics }) => {
  return (
    <div
      className="border border-green-500 rounded-lg shadow-lg bg-gray-800 flex flex-col justify-between items-center"
      style={{ width: '300px', height: '400px', padding: '20px' }}
    >
      <h2 className="text-xl font-bold text-green-500 mb-4 text-center w-full">{song_name}</h2>
      <div 
        className="flex-grow flex items-center justify-center overflow-y-auto w-full b-10 "
        style={{ fontSize: 'clamp(0.8rem, 1vw, 1rem)' }}
      >
        <p className="text-gray-400 text-center whitespace-pre-wrap">
          {censoredLyrics}
        </p>
      </div>
    </div>
  );
};

export default CensoredLyricsCard;
