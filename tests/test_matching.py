import numpy as np
import soundfile as sf
import librosa
import requests
import os


def add_noise(path: str, snr_db: float, out_path: str):
    """Add white noise at a given SNR (dB) to simulate noisy environment."""
    y, sr = librosa.load(path, sr=22050, mono=True)
    signal_power = np.mean(y ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), len(y))
    sf.write(out_path, y + noise, sr)
    return out_path


def test_identify(audio_path: str, api_url: str = "http://localhost:8000/identify"):
    with open(audio_path, "rb") as f:
        response = requests.post(api_url, files={"file": (os.path.basename(audio_path), f, "audio/wav")})
    return response.json()


if __name__ == "__main__":
    SOURCE = "data/songs/test.wav"   # replace with an actual ingested song
    if not os.path.exists(SOURCE):
        print(f"Place a test file at {SOURCE} and re-run.")
        exit(1)

    for snr in [20, 10, 5]:
        noisy = f"noisy_{snr}db.wav"
        add_noise(SOURCE, snr_db=snr, out_path=noisy)
        result = test_identify(noisy)
        print(f"SNR {snr:2d}dB → {result}")
        os.remove(noisy)
