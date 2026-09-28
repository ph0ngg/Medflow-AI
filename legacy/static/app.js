/**
 * MedFlow AI - Kiosk Frontend App
 * Quản lý UI, camera, voice và giao tiếp với backend.
 */

const API_BASE = "/api/kiosk";

// ── State ────────────────────────────────────────────
const state = {
    sessionId: null,
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    stream: null,
};

// ── DOM Elements ─────────────────────────────────────
const screens = {
    idle:      document.getElementById("screen-idle"),
    chat:      document.getElementById("screen-chat"),
    result:    document.getElementById("screen-result"),
    emergency: document.getElementById("screen-emergency"),
};

const cameraFeed = document.getElementById("camera-feed");
const cameraCanvas = document.getElementById("camera-canvas");
const chatMessages = document.getElementById("chat-messages");
const textInput = document.getElementById("text-input");
const resultContent = document.getElementById("result-content");
const emergencyMessage = document.getElementById("emergency-message");

// ── Navigation ───────────────────────────────────────
function showScreen(name) {
    Object.values(screens).forEach(s => s.classList.remove("active"));
    if (screens[name]) screens[name].classList.add("active");
}

// ── Camera ───────────────────────────────────────────
async function startCamera() {
    try {
        state.stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user", width: 640, height: 480 },
            audio: true,
        });
        cameraFeed.srcObject = state.stream;

        // Định kỳ gửi frame để detect face
        setInterval(captureAndDetect, 1500);
    } catch (err) {
        console.error("Camera error:", err);
        addChatMessage("system", "⚠️ Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.");
    }
}

/** Tắt toàn bộ video track sau khi đã xác thực khuôn mặt. */
function stopVideoTracks() {
    if (!state.stream) return;
    state.stream.getVideoTracks().forEach(track => track.stop());
}

async function captureAndDetect() {
    if (state.sessionId) return; // Đã có session, không cần detect nữa

    const canvas = cameraCanvas;
    const ctx = canvas.getContext("2d");
    canvas.width = cameraFeed.videoWidth || 640;
    canvas.height = cameraFeed.videoHeight || 480;
    ctx.drawImage(cameraFeed, 0, 0);

    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    try {
        const res = await fetch(`${API_BASE}/detect-face`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.detected && data.faces.length > 0) {
            const face = data.faces[0];
            if (face.name) {
                // Nhận diện được → tự động bắt đầu session
                await startSession(face.name, face.id);
            } else {
                // Có khuôn mặt nhưng không nhận diện được → người mới
                await startSession(null, null);
            }
        }
    } catch (err) {
        console.error("Detect error:", err);
    }
}

// ── Session ──────────────────────────────────────────
async function startSession(faceName, faceId) {
    if (state.sessionId) return;

    const formData = new FormData();
    if (faceName) formData.append("face_name", faceName);
    if (faceId) formData.append("face_id", faceId);

    const res = await fetch(`${API_BASE}/start-session`, { method: "POST", body: formData });
    const data = await res.json();

    state.sessionId = data.session_id;

    // Tắt video track — không cần camera sau khi đã xác thực
    stopVideoTracks();

    if (data.is_returning) {
        // Bệnh nhân cũ → chuyển sang màn hình chat + chào hỏi
        showScreen("chat");
        addChatMessage("system", data.greeting || `Xin chào ${data.patient_name}!`);
    } else {
        // Bệnh nhân mới → màn hình chat
        showScreen("chat");
        addChatMessage("system", data.message || "Chào mừng! Vui lòng mô tả triệu chứng của bạn.");
    }
}

// ── Chat ─────────────────────────────────────────────
function addChatMessage(role, text) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.parentElement.scrollTop = chatMessages.parentElement.scrollHeight;
}

async function sendMessage(text) {
    if (!state.sessionId || !text.trim()) return;

    addChatMessage("user", text);

    const res = await fetch(`${API_BASE}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: state.sessionId, message: text }),
    });
    const data = await res.json();

    handleResponse(data);
}

function handleResponse(data) {
    // Hiển thị phản hồi
    if (data.response) {
        const role = data.intent === "emergency" ? "emergency" : "system";
        addChatMessage(role, data.response);

        // TTS (tùy chọn - bật mic để nghe)
        // playTTS(data.response);
    }

    // Xử lý theo state
    switch (data.state) {
        case "emergency":
            showScreen("emergency");
            emergencyMessage.textContent = data.response;
            break;

        case "triaging":
            if (data.suggested_department && data.queue_info) {
                const qi = data.queue_info;
                addChatMessage("system",
                    `📋 Đề xuất: ${data.suggested_department}\n` +
                    `👥 Đang chờ: ${qi.current_queue} người\n` +
                    `⏱️ Thời gian chờ: ~${qi.estimated_wait} phút\n\n` +
                    `Bạn có muốn đăng ký khám tại khoa này không? (gõ "có" hoặc "không")`
                );
            }
            break;

        case "issuing":
            if (data.ticket) {
                showScreen("result");
                resultContent.innerHTML = `
                    <h2>✅ Đăng ký thành công!</h2>
                    <p class="ticket-number">#${data.ticket.ticket_number}</p>
                    <p class="dept-info">
                        📍 ${data.ticket.department}<br>
                        ⏱️ Thời gian chờ dự kiến: ${data.ticket.estimated_wait} phút
                    </p>
                `;
            }
            break;

        case "done":
            showScreen("result");
            break;
    }
}

// ── Voice Recording ──────────────────────────────────
const AUDIO_MIME_TYPES = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
    "audio/mpeg",
];

/** Trả về MIME type đầu tiên được browser hỗ trợ, hoặc "" để dùng default. */
function getSupportedMimeType() {
    for (const mime of AUDIO_MIME_TYPES) {
        if (MediaRecorder.isTypeSupported(mime)) return mime;
    }
    return ""; // fallback: để browser tự chọn
}

async function startRecording() {
    if (!state.stream) return;

    // Đảm bảo stream có audio track
    const audioTracks = state.stream.getAudioTracks();
    if (audioTracks.length === 0) {
        addChatMessage("system", "⚠️ Không tìm thấy microphone.");
        return;
    }

    // Tách audio track ra stream riêng — một số browser lỗi nếu stream có cả video
    const audioStream = new MediaStream(audioTracks);

    state.audioChunks = [];
    const mimeType = getSupportedMimeType();
    const options = mimeType ? { mimeType } : {};
    state.recorderMimeType = mimeType || "audio/webm"; // lưu lại cho Blob

    try {
        state.mediaRecorder = new MediaRecorder(audioStream, options);
    } catch (err) {
        console.error("MediaRecorder error:", err);
        addChatMessage("system", "⚠️ Trình duyệt không hỗ trợ ghi âm.");
        return;
    }

    state.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) state.audioChunks.push(e.data);
    };

    state.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(state.audioChunks, { type: state.recorderMimeType });
        await sendVoice(audioBlob);
    };

    try {
        state.mediaRecorder.start();
    } catch (err) {
        console.error("MediaRecorder start error:", err);
        addChatMessage("system", "⚠️ Không thể bắt đầu ghi âm.");
        return;
    }

    state.isRecording = true;
    document.getElementById("btn-voice").classList.add("recording");
}

async function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        document.getElementById("btn-voice").classList.remove("recording");
    }
}

async function sendVoice(audioBlob) {
    if (!state.sessionId) {
        addChatMessage("system", "⚠️ Vui lòng đứng trước camera để bắt đầu.");
        return;
    }

    const formData = new FormData();
    formData.append("session_id", state.sessionId);
    formData.append("audio", audioBlob, "voice.webm");

    try {
        const res = await fetch(`${API_BASE}/voice-message`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.transcribed_text) {
            addChatMessage("user", `🎤 ${data.transcribed_text}`);
        }
        handleResponse(data);
    } catch (err) {
        console.error("Voice error:", err);
        addChatMessage("system", "⚠️ Lỗi xử lý giọng nói.");
    }
}

// ── TTS (Text-to-Speech) ─────────────────────────────
async function playTTS(text) {
    try {
        const res = await fetch(`${API_BASE}/tts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: state.sessionId || "", message: text }),
        });
        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    } catch (err) {
        console.error("TTS error:", err);
    }
}

// ── Event Listeners ──────────────────────────────────
document.getElementById("btn-send").addEventListener("click", () => {
    const text = textInput.value.trim();
    if (text) {
        sendMessage(text);
        textInput.value = "";
    }
});

textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        const text = textInput.value.trim();
        if (text) {
            sendMessage(text);
            textInput.value = "";
        }
    }
});

document.getElementById("btn-voice").addEventListener("mousedown", startRecording);
document.getElementById("btn-voice").addEventListener("mouseup", stopRecording);
document.getElementById("btn-voice").addEventListener("touchstart", (e) => {
    e.preventDefault();
    startRecording();
});
document.getElementById("btn-voice").addEventListener("touchend", stopRecording);

document.getElementById("btn-new-session").addEventListener("click", () => {
    if (state.sessionId) {
        fetch(`${API_BASE}/end-session`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: state.sessionId }),
        });
    }
    state.sessionId = null;
    chatMessages.innerHTML = "";
    showScreen("idle");
});

document.getElementById("btn-emergency-ok").addEventListener("click", () => {
    if (state.sessionId) {
        fetch(`${API_BASE}/end-session`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: state.sessionId }),
        });
    }
    state.sessionId = null;
    chatMessages.innerHTML = "";
    showScreen("idle");
});

// ── Init ─────────────────────────────────────────────
startCamera();
showScreen("idle");
