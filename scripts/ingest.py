import os
import sys
import librosa
from tqdm import tqdm
from app.database import init_db, insert_song, insert_fingerprints
from app.fingerprint import fingerprint_audio

SONGS_DIR = "data/songs"


def ingest_file(path: str):
    name = os.path.splitext(os.path.basename(path))[0]
    parts = name.split(" - ", 1)
    title = parts[0].strip()
    artist = parts[1].strip() if len(parts) > 1 else "Unknown"
    
    try:
        duration = librosa.get_duration(path=path)
        song_id = insert_song(title, artist, duration)
        hashes = fingerprint_audio(path)
        insert_fingerprints(song_id, hashes)
        return True, f"{title} by {artist} - {len(hashes)} hashes"
    except Exception as e:
        return False, f"{title} - ERROR: {str(e)}"


def ingest_all():
    init_db()

    # Ingest from data/songs/ folder
    folder_files = [
        os.path.join(SONGS_DIR, f)
        for f in os.listdir(SONGS_DIR)
        if f.endswith((".mp3", ".wav", ".flac"))
    ]

    extra_files = [
        r"C:\Users\Bhumika U\Downloads\panic_alarm.mp3",
        r"C:\Users\Bhumika U\Downloads\Panic Alarm.mp3",
    ]
    all_files = folder_files + [f for f in extra_files if os.path.exists(f)]
    
    if not all_files:
        print("No audio files found to ingest.")
        return

    print(f"\nIngesting {len(all_files)} song(s)...\n")
    
    success_count = 0
    failed_count = 0
    
    for path in tqdm(all_files, desc="Processing", unit="song"):
        success, message = ingest_file(path)
        if success:
            success_count += 1
            tqdm.write(f"[OK] {message}")
        else:
            failed_count += 1
            tqdm.write(f"[FAIL] {message}")

    print(f"\n{'='*60}")
    print(f"Done. Successfully ingested: {success_count}/{len(all_files)} songs")
    if failed_count > 0:
        print(f"Failed: {failed_count} songs")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        ingest_all()
    except KeyboardInterrupt:
        print("\n\nIngestion interrupted by user.")
        sys.exit(1)
