import os
import tempfile
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from app.matcher import match
from app.database import init_db, get_conn

app = FastAPI(title="Mini Shazam")

app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/ui/index.html")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/songs")
def list_songs():
    with get_conn() as conn:
        rows = conn.execute("SELECT id, title, artist, duration FROM songs").fetchall()
    return [{"id": r[0], "title": r[1], "artist": r[2], "duration": r[3]} for r in rows]


@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    raw = await file.read()
    mime = file.content_type or ""
    if "webm" in mime or "ogg" in mime:
        ext = ".webm"
    elif "mp3" in mime or "mpeg" in mime:
        ext = ".mp3"
    elif "flac" in mime:
        ext = ".flac"
    else:
        ext = os.path.splitext(file.filename)[-1].lower() or ".wav"

    in_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    in_tmp.write(raw)
    in_tmp.close()
    out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    out_tmp.close()

    try:
        AudioSegment.from_file(in_tmp.name).export(out_tmp.name, format="wav")
        result = match(out_tmp.name)
        if not result.get("song_id"):
            return JSONResponse({"match": None, "confidence": 0, "message": "No match found"})
        with get_conn() as conn:
            row = conn.execute(
                "SELECT title, artist FROM songs WHERE id=?", (result["song_id"],)
            ).fetchone()
        return {
            "title": row[0],
            "artist": row[1],
            "confidence": result["confidence"],
            "matched_hashes": result["matched_hashes"],
            "total_query_hashes": result["total_query_hashes"],
        }
    finally:
        if os.path.exists(in_tmp.name):
            os.unlink(in_tmp.name)
        if os.path.exists(out_tmp.name):
            os.unlink(out_tmp.name)
