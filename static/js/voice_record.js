let startTime;
let timerInterval;
let mediaRecorder;
let audioChunks = [];

document.addEventListener("DOMContentLoaded", () => {
    const recordbtn = document.getElementById("recordbtn");
    const stopbtn = document.getElementById("stopbtn");
    const refreshbtn = document.getElementById("refreshbtn");
    const recordingText = document.getElementById("recording-text");
    const recordingTimer = document.getElementById("recording-timer");
    const micStatus = document.getElementById("mic-status");
    const voiceInput = document.getElementById("voice_record");
    const audioPlayback = document.getElementById("audioPlayback");
    const verifyBtn = document.getElementById("verifybtn");

    verifyBtn.disabled = true;

    
    recordbtn.addEventListener("click", startRecording);
    console.log("Record button clicked")

    
    stopbtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
        stopRecordingTimer();
        updateMicStatus("Recording stopped", false);
        toggleButtons(false);
    console.log("Stop button clicked")    
    });

    
    refreshbtn.addEventListener("click", () => {
        stopRecordingTimer();
        voiceInput.value = "";
        audioPlayback.src = "";
        audioPlayback.style.display = "none";
        updateMicStatus("Not recording", false);
        toggleButtons(false);
        verifyBtn.disabled = true;
        const verifyMessage = document.getElementById("verify-message");
        if (verifyMessage) verifyMessage.textContent = "";
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (e) => {
                audioChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const blob = new Blob(audioChunks, { type: "audio/webm" });
                const base64Audio = await blobToBase64(blob);

                voiceInput.value = "data:audio/webm;base64," + base64Audio;
                console.log("Base64 length:",voiceInput.value.length);
                audioPlayback.src = URL.createObjectURL(blob);
                audioPlayback.style.display = "block";
                verifyBtn.disabled = false;
                console.log("Recording stopped. Chunks:", audioChunks.length);
            };

            mediaRecorder.start();
            startRecordingTimer();
            updateMicStatus("Recording...", true);
            toggleButtons(true);
        } catch (err) {
            alert("Microphone access denied or not supported by your browser.");
            console.error("Microphone error:", err);
        }
    }

    function toggleButtons(isRecording) {
        recordbtn.disabled = isRecording;
        stopbtn.disabled = !isRecording;
    }

    function updateMicStatus(text, isRecording) {
        recordingText.textContent = text;
        micStatus.classList.toggle("mic-recording", isRecording);
        micStatus.classList.toggle("mic-idle", !isRecording);
    }

    function startRecordingTimer() {
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
            const seconds = String(elapsed % 60).padStart(2, "0");
            recordingTimer.textContent = `${minutes}:${seconds}`;
        }, 1000);
    }

    function stopRecordingTimer() {
        clearInterval(timerInterval);
        recordingTimer.textContent = "00:00";
    }

    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result.split(",")[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
});
