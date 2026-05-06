import librosa
import numpy as np
from scipy.ndimage import maximum_filter
import hashlib

# --- Config ---
SR = 22050
N_FFT = 4096
HOP = 512
PEAK_NEIGHBORHOOD = 20
FAN_VALUE = 15
TIME_DELTA_MIN = 1
TIME_DELTA_MAX = 200
FREQ_DELTA_MAX = 128


def load_audio(path: str) -> np.ndarray:
    y, _ = librosa.load(path, sr=SR, mono=True)
    y = librosa.util.normalize(y)
    return y


def get_spectrogram(y: np.ndarray) -> np.ndarray:
    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP))
    return librosa.amplitude_to_db(S, ref=np.max)


def get_peaks(S: np.ndarray) -> list[tuple[int, int]]:
    """Return (freq_bin, time_bin) of local maxima above threshold."""
    local_max = maximum_filter(S, size=PEAK_NEIGHBORHOOD) == S
    bg = S < (S.mean() + S.std())
    peaks = local_max & ~bg
    freq_idx, time_idx = np.where(peaks)
    return list(zip(freq_idx.tolist(), time_idx.tolist()))


def generate_hashes(peaks: list[tuple[int, int]]) -> list[tuple[str, int]]:
    """
    Combinatorial hashing: pair each anchor with FAN_VALUE neighbors.
    Returns list of (hash_hex, anchor_time_offset).
    """
    peaks_sorted = sorted(peaks, key=lambda x: x[1])
    hashes = []
    for i, (f1, t1) in enumerate(peaks_sorted):
        for f2, t2 in peaks_sorted[i + 1: i + 1 + FAN_VALUE]:
            dt = t2 - t1
            if not (TIME_DELTA_MIN <= dt <= TIME_DELTA_MAX):
                continue
            if abs(f2 - f1) > FREQ_DELTA_MAX:
                continue
            key = f"{f1}|{f2}|{dt}"
            h = hashlib.sha1(key.encode()).hexdigest()[:20]
            hashes.append((h, t1))
    return hashes


def fingerprint_audio(path: str) -> list[tuple[str, int]]:
    y = load_audio(path)
    S = get_spectrogram(y)
    peaks = get_peaks(S)
    return generate_hashes(peaks)
