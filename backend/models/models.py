from pydantic import BaseModel
from typing import List, Optional

class Song(BaseModel):
    id: str
    name: str
    lyrics: Optional[str] = None
    lang: Optional[str] = None
    external_urls: Optional[str] = None

class SongPoolRequest(BaseModel):
    songs: List[Song]
    N: int
    
class LyricsRequest(BaseModel):
    songs: List[Song]
    
class ScoreRequest(BaseModel):
    user_input : List[str]
    user_answers : List[str]
    censorship : List[str]
    answers : List[str]
    
class QuestionRequest(BaseModel):
    artist : str
    song : Song