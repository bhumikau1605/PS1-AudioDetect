from collections import defaultdict
from app.database import query_hashes as db_query_hashes
from app.fingerprint import fingerprint_audio


def match(query_path: str) -> dict:
    query_hashes = fingerprint_audio(query_path)
    if not query_hashes:
        return {"match": None, "confidence": 0}

    hash_map = {h: t for h, t in query_hashes}
    db_results = db_query_hashes(list(hash_map.keys()))

    # Time-coherence voting: count aligned time deltas per song
    votes = defaultdict(int)
    for h, song_id, db_offset in db_results:
        query_offset = hash_map.get(h)
        if query_offset is not None:
            delta = db_offset - query_offset
            votes[(song_id, delta)] += 1

    if not votes:
        return {"match": None, "confidence": 0}

    best_key, best_count = max(votes.items(), key=lambda x: x[1])
    best_song_id = best_key[0]
    total_query_hashes = len(query_hashes)
    confidence = min(100.0, round((best_count / total_query_hashes) * 100 * 5, 2))

    return {
        "song_id": best_song_id,
        "confidence": confidence,
        "matched_hashes": best_count,
        "total_query_hashes": total_query_hashes,
    }
