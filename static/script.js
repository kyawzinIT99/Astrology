/* ═══════════════════════════════════════════════════════════
   Myanmar Astrology Chatbot — Frontend Logic
   ═══════════════════════════════════════════════════════════ */

const chatMessages = document.getElementById('chatMessages');
const chatArea = document.getElementById('chatArea');
const userInput = document.getElementById('userInput');
const btnSend = document.getElementById('btnSend');
const pdfDownloadArea = document.getElementById('pdfDownloadArea');
const inputHint = document.getElementById('inputHint');

let isProcessing = false;
let currentState = 'greeting';

// ── Initialize ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    createStars();
    initChat();
});

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ── Stars Background ────────────────────────────────────────
function createStars() {
    const container = document.getElementById('starsContainer');
    const count = 80;
    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.setProperty('--duration', (2 + Math.random() * 4) + 's');
        star.style.setProperty('--max-opacity', (0.3 + Math.random() * 0.7).toString());
        star.style.animationDelay = Math.random() * 4 + 's';
        star.style.width = (1 + Math.random() * 2) + 'px';
        star.style.height = star.style.width;
        container.appendChild(star);
    }
}

// ── Chat Initialization ─────────────────────────────────────
async function initChat() {
    showTyping();
    try {
        const res = await fetch('/api/init');
        const data = await res.json();
        removeTyping();
        addMessage('bot', data.response);
        currentState = data.state;
        updateHint();
    } catch (err) {
        removeTyping();
        addMessage('bot', '❌ ဆာဗာနှင့် ချိတ်ဆက်၍ မရပါ။ ထပ်မံကြိုးစားပါ။');
    }
}

// ── Send Message ────────────────────────────────────────────
async function sendMessage() {
    const msg = userInput.value.trim();
    if (!msg || isProcessing) return;

    isProcessing = true;
    btnSend.disabled = true;
    userInput.value = '';

    addMessage('user', msg);
    showTyping();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();

        // Simulate a slight delay for natural feel
        await new Promise(r => setTimeout(r, 400 + Math.random() * 600));

        removeTyping();
        addMessage('bot', data.response);
        currentState = data.state;

        updateHint();
    } catch (err) {
        removeTyping();
        addMessage('bot', '❌ တစ်စုံတစ်ခု မှားယွင်းနေပါသည်။ ထပ်မံကြိုးစားပါ။');
    }

    isProcessing = false;
    btnSend.disabled = false;
    userInput.focus();
}

// ── Add Message ─────────────────────────────────────────────
function addMessage(role, content) {
    const msg = document.createElement('div');
    msg.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'bot' ? '🔮' : '👤';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMessage(content);

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chatMessages.appendChild(msg);

    scrollToBottom();
}

// ── Format Message ──────────────────────────────────────────
function formatMessage(text) {
    // Escape HTML
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: _text_
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');

    // Links: [text](url)
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" style="color: var(--accent-gold); text-decoration: underline;">$1</a>');

    // Inline code: `text`
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    // Separator lines
    html = html.replace(/═{3,}/g, '<span class="msg-separator"></span>');

    return html;
}

// ── Typing Indicator ────────────────────────────────────────
function showTyping() {
    const msg = document.createElement('div');
    msg.className = 'message bot';
    msg.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🔮';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    msg.appendChild(avatar);
    msg.appendChild(bubble);
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

// ── Scroll ──────────────────────────────────────────────────
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

// ── Input Hint ──────────────────────────────────────────────
function updateHint() {
    const hints = {
        'greeting': 'သင့်ရဲ့ အမည်ကို ရိုက်ထည့်ပေးပါ',
        'ask_dob': 'မွေးနေ့ ရက်စွဲကို YYYY-MM-DD ပုံစံဖြင့် ရိုက်ထည့်ပါ',
        'ask_wednesday': 'နံနက် သို့မဟုတ် ညနေ ဟု ရိုက်ထည့်ပါ',
        'reading_shown': 'ဟုတ်ကဲ့ (ဟောစာတမ်း) ဟု ရိုက်ထည့်ပါ',
        'forecast_shown': 'ရက်ချိန်း ဟု ရိုက်ထည့်၍ ရက်ချိန်း ယူပါ',
    };
    inputHint.textContent = hints[currentState] || '';
}

// ── PDF Download ────────────────────────────────────────────
async function downloadPDF() {
    try {
        const res = await fetch('/api/generate-pdf', { method: 'POST' });
        if (!res.ok) throw new Error('PDF generation failed');

        const arrayBuffer = await res.arrayBuffer();
        const blob = new Blob([arrayBuffer], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);

        // Extract filename from Content-Disposition header or use default
        const disposition = res.headers.get('Content-Disposition');
        let filename = 'mahabote_report.pdf';
        if (disposition) {
            const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';\n]+)/i);
            if (match) filename = decodeURIComponent(match[1]);
        }

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        addMessage('bot', '✅ PDF ဟောစာတမ်း ဒေါင်းလုဒ် အောင်မြင်ပါပြီ! 🎉');
    } catch (err) {
        addMessage('bot', '❌ PDF ဖန်တီးရာတွင် အမှားရှိပါသည်။ ထပ်မံကြိုးစားပါ။');
    }
}

// ── Reset Chat ──────────────────────────────────────────────
function resetChat() {
    chatMessages.innerHTML = '';
    currentState = 'greeting';
    // Clear server session
    fetch('/api/init').then(res => res.json()).then(data => {
        addMessage('bot', data.response);
        currentState = data.state;
        updateHint();
    });
}

// ── Developer Modal ─────────────────────────────────────────
function toggleDevModal() {
    const modal = document.getElementById('devModal');
    if (modal) {
        modal.classList.toggle('active');
    }
}
