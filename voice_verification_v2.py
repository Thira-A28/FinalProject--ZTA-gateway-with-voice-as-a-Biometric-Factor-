import os
import numpy as np
import librosa
import soundfile as sf
from scipy.spatial.distance import cosine
import noisereduce as nr

# ----------- SETTINGS -----------
CLEAN_DIR = "pre_recorded_clean"  
os.makedirs(CLEAN_DIR, exist_ok=True)

# ----------- NOISE REDUCTION -----------
def clean_audio(input_path, output_path):
    try:
        y, sr = librosa.load(input_path, sr=16000, mono=True)
        reduced = nr.reduce_noise(y=y, sr=sr)
        sf.write(output_path, reduced, sr)
        print(f"[CLEAN] {os.path.basename(input_path)} -> {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to clean {input_path}: {e}")

def batch_clean_pre_recorded():
    """Clean all files inside pre_recorded/ and save to pre_recorded_clean/."""
    base_dir = "pre_recorded"
    for fname in os.listdir(base_dir):
        if fname.lower().endswith((".wav", ".mp3", ".webm")):
            inp = os.path.join(base_dir, fname)
            outp = os.path.join(CLEAN_DIR, fname.replace(".mp3", ".wav").replace(".webm", ".wav"))
            clean_audio(inp, outp)

# ----------- FEATURE EXTRACTION -----------
def extract_mfcc(file_path):
    y, sr = librosa.load(file_path, sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=30)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1)

# ----------- VERIFICATION -----------
def verify_user_voice(test_path, reference_path, euclid_threshold=55.0, cos_threshold=0.93):
    try:
        
        temp_clean_test = test_path.replace(".wav", "_cleaned.wav")
        clean_audio(test_path, temp_clean_test)

        test_features = extract_mfcc(temp_clean_test)
        ref_features = extract_mfcc(reference_path)

        euclid = np.linalg.norm(test_features - ref_features)
        cos_sim = 1 - cosine(test_features, ref_features)

        print("[DEBUG] Test MFCC:", test_features[:5])
        print("[DEBUG] Ref MFCC:", ref_features[:5])
        print(f"[VOICE] euclid={euclid:.2f}, cosine={cos_sim:.3f}, "
              f"(thr_e={euclid_threshold}, thr_c={cos_threshold})")

        os.remove(temp_clean_test)  

        return (euclid < euclid_threshold) and (cos_sim > cos_threshold)
    except Exception as e:
        print("Verification error:", e)
        return False
