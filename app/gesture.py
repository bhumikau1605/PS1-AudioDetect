import cv2
import mediapipe as mp
import sounddevice as sd
import soundfile as sf
import numpy as np

SAMPLE_RATE = 44100

HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


def count_extended_fingers(hand_landmarks) -> int:
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    count = sum(
        1 for tip, pip in zip(tips, pips)
        if hand_landmarks[tip].y < hand_landmarks[pip].y
    )
    if hand_landmarks[4].x < hand_landmarks[3].x:
        count += 1
    return count


def gesture_record(output_path: str = "query.wav", max_seconds: int = 10):
    import urllib.request, os
    model_path = "hand_landmarker.task"
    if not os.path.exists(model_path):
        print("Downloading hand landmarker model...")
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            model_path
        )

    options = HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE,
        num_hands=1,
    )

    cap = cv2.VideoCapture(0)
    recording, frames = False, []
    stream = None

    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect(mp_image)

            fingers = 0
            if result.hand_landmarks:
                fingers = count_extended_fingers(result.hand_landmarks[0])

            if fingers == 5 and not recording:
                recording = True
                print("Recording started (open palm detected)")
                stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1)
                stream.start()

            if fingers == 0 and recording:
                recording = False
                stream.stop()
                stream.close()
                audio = np.concatenate(frames)
                sf.write(output_path, audio, SAMPLE_RATE)
                print(f"Recording saved to {output_path}")
                break

            if recording and stream:
                chunk, _ = stream.read(1024)
                frames.append(chunk)

            label = "REC 🔴" if recording else "IDLE"
            cv2.putText(frame, f"Fingers: {fingers} | {label}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Gesture Control — Open Palm=Start, Fist=Stop", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    return output_path
