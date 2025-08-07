from flask import Flask, render_template, redirect, url_for, request, session, flash
import base64
import os
import traceback
from voice_verification_v2 import verify_user_voice
from user_auth import find_user_by_email, is_access_allowed
from pydub import AudioSegment
from pydub.utils import which

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")


AudioSegment.converter = which("ffmpeg")


TMP_DIR = os.path.join(app.root_path, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)


CLEANED_DIR = os.path.join(app.root_path, "pre_recorded_clean")
os.makedirs(CLEANED_DIR, exist_ok=True)

# ---------------------- DEBUG SESSION RESET ----------------------
@app.before_request
def debug_session_info():
    print(f"[DEBUG] Request Path: {request.path}, Method: {request.method}")
    print(f"[DEBUG] Session Data: {dict(session)}")


# ---------------------- LOGIN ----------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        print(f"[LOGIN] Attempt with email={email}")

        user = find_user_by_email(email)
        if user and password == user['password']:
            print("[LOGIN] Password OK -> redirecting to voice_auth")
            session['email'] = email
            session['user'] = user
            return redirect(url_for('voice_auth'))
        else:
            print("[LOGIN] Invalid credentials")
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')


# ---------------------- VOICE AUTH ----------------------
@app.route('/voice_auth', methods=['GET', 'POST'])
def voice_auth():
    if request.method == 'GET':
        return render_template('voice_auth.html')

    print("[VOICE AUTH] POST triggered")

    email = session.get('email')
    if not email:
        print("[VOICE AUTH] No email in session -> redirect to login")
        return redirect(url_for('login'))

    audio_data = request.form.get('voiceData')
    if not audio_data:
        print("[VOICE AUTH] No voice data received")
        return render_template('voice_auth.html', error="No voice data received.")

    try:
       
        if ',' in audio_data:
            audio_data = audio_data.split(',', 1)[1]

        audio_bytes = base64.b64decode(audio_data)
        temp_webm = os.path.join(TMP_DIR, f"user_{email}_new.webm")
        temp_wav = os.path.join(TMP_DIR, f"user_{email}_new.wav")

        with open(temp_webm, 'wb') as f:
            f.write(audio_bytes)
        print(f"[VOICE] Saved temp webm: {temp_webm} ({len(audio_bytes)} bytes)")

        
        audio = AudioSegment.from_file(temp_webm)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(temp_wav, format="wav")
        print(f"[VOICE] Converted to wav: {temp_wav}")

        
        user = session.get('user') or find_user_by_email(email)
        ref_path = os.path.join(CLEANED_DIR, user['voice_sample'])

        if not os.path.exists(ref_path):
            print(f"[VOICE] Reference file not found at {ref_path}")
            return render_template('voice_auth.html', error="Reference voice file missing. Please contact admin.")

        print(f"[VOICE] Reference path: {ref_path}")

        
        is_verified = verify_user_voice(temp_wav, ref_path)
        print(f"[VOICE] Verification result: {is_verified}")

        
        for p in (temp_webm, temp_wav):
            try:
                os.remove(p)
            except OSError:
                pass

        if not is_verified:
            print("[VOICE] FAILED -> Returning to voice_auth page")
            return render_template('voice_auth.html', error="Voice authentication failed.")

        
        current_ip = request.remote_addr
        ok, reason = is_access_allowed(user, current_ip, return_reason=True)
        print(f"[ACCESS] IP={current_ip} -> ok={ok}, reason='{reason}'")
        if not ok:
            return render_template('voice_auth.html', error=f"Access denied")

        # Success
        session['authenticated'] = True
        flash('✅ Access Granted: Voice verified and contextual access granted.', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        traceback.print_exc()
        flash(f"Voice authentication failed: {e}", "error")
        return redirect(url_for('voice_auth'))


# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        print("[DASHBOARD] Not authenticated -> redirecting to voice_auth")
        return redirect(url_for('voice_auth'))
    return render_template('dashboard.html')


# ---------------------- LOGOUT ----------------------
@app.route('/logout')
def logout():
    print("[LOGOUT] Clearing session")
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
