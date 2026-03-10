// API Configuration
const API_BASE = window.location.origin;

// State
let conversations = [];
let currentMessages = [];
let isLoading = false;
let currentUser = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    checkAuth();
    loadConversationsFromStorage();
    await loadStats();
    updateConversationsList();
    console.log('ZenBot initialized');
});

// Authentication
function checkAuth() {
    const user = localStorage.getItem('zenbot_user');
    if (user) {
        currentUser = JSON.parse(user);
        showMainApp();
        updateUserDisplay();
    } else {
        showAuthScreen();
    }
}

function showAuthScreen() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

function showMainApp() {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
}

function updateUserDisplay() {
    if (currentUser) {
        document.getElementById('userInfo').innerHTML = `
            <div class="flex items-center gap-3 bg-slate-800 rounded-lg p-3">
                <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center font-bold text-sm">
                    ${currentUser.name.charAt(0).toUpperCase()}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold truncate">${escapeHtml(currentUser.name)}</div>
                    <div class="text-xs text-slate-400 truncate">${escapeHtml(currentUser.email)}</div>
                </div>
                <button onclick="logout()" class="text-slate-400 hover:text-white transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                </button>
            </div>
        `;
    }
}

function showSignUp() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('signupForm').classList.remove('hidden');
}

function showLogin() {
    document.getElementById('signupForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
}

function handleSignUp(event) {
    event.preventDefault();
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;

    if (!name || !email || !password) {
        alert('Please fill in all fields');
        return;
    }

    // Check if user exists
    const users = JSON.parse(localStorage.getItem('zenbot_users') || '[]');
    if (users.find(u => u.email === email)) {
        alert('User with this email already exists');
        return;
    }

    // Create user
    const user = { name, email, password, createdAt: new Date().toISOString() };
    users.push(user);
    localStorage.setItem('zenbot_users', JSON.stringify(users));

    // Login user
    currentUser = { name, email };
    localStorage.setItem('zenbot_user', JSON.stringify(currentUser));

    showMainApp();
    updateUserDisplay();
}

function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    const users = JSON.parse(localStorage.getItem('zenbot_users') || '[]');
    const user = users.find(u => u.email === email && u.password === password);

    if (!user) {
        alert('Invalid email or password');
        return;
    }

    // Login user
    currentUser = { name: user.name, email: user.email };
    localStorage.setItem('zenbot_user', JSON.stringify(currentUser));

    showMainApp();
    updateUserDisplay();
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('zenbot_user');
        currentUser = null;
        conversations = [];
        currentMessages = [];
        showAuthScreen();
    }
}

// Load Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        document.getElementById('stats').innerHTML = `
            <div class="text-slate-400 font-medium mb-2">System Status</div>
            <div class="grid grid-cols-2 gap-2">
                <div>
                    <div class="text-slate-500 text-xs">Chunks</div>
                    <div class="text-white font-semibold">${data.total_chunks.toLocaleString()}</div>
                </div>
                <div>
                    <div class="text-slate-500 text-xs">Vectors</div>
                    <div class="text-white font-semibold">${data.vector_dimensions}D</div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Storage Management
function saveConversationsToStorage() {
    if (currentUser) {
        const storageKey = `zenbot_conversations_${currentUser.email}`;
        localStorage.setItem(storageKey, JSON.stringify(conversations));
    }
}

function loadConversationsFromStorage() {
    if (currentUser) {
        const storageKey = `zenbot_conversations_${currentUser.email}`;
        const stored = localStorage.getItem(storageKey);
        if (stored) {
            conversations = JSON.parse(stored);
        }
    }
}

// New Chat
function newChat() {
    if (currentMessages.length > 0) {
        // Save current conversation
        const title = currentMessages[0].content.substring(0, 50);
        conversations.unshift({
            id: Date.now(),
            title,
            messages: [...currentMessages],
            timestamp: new Date().toISOString()
        });
        saveConversationsToStorage();
        updateConversationsList();
    }

    currentMessages = [];
    showWelcome();
}

// Update Conversations List
function updateConversationsList() {
    const container = document.getElementById('conversations');

    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-slate-600 text-sm">
                No conversations yet
            </div>
        `;
        return;
    }

    container.innerHTML = conversations.map(conv => `
        <button
            onclick="loadConversation(${conv.id})"
            class="w-full text-left px-4 py-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors text-sm group">
            <div class="flex items-start justify-between gap-2">
                <div class="flex items-start gap-2 flex-1 min-w-0">
                    <svg class="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
                    </svg>
                    <span class="text-slate-300 line-clamp-2 flex-1">${escapeHtml(conv.title)}</span>
                </div>
                <button onclick="deleteConversation(event, ${conv.id})" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-all">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>
            </div>
        </button>
    `).join('');
}

// Delete Conversation
function deleteConversation(event, id) {
    event.stopPropagation();
    if (confirm('Delete this conversation?')) {
        conversations = conversations.filter(c => c.id !== id);
        saveConversationsToStorage();
        updateConversationsList();

        // If current conversation is deleted, show welcome
        if (currentMessages.length > 0 && currentMessages[0].timestamp) {
            const currentId = conversations.find(c =>
                c.messages[0].timestamp === currentMessages[0].timestamp
            )?.id;
            if (currentId === id) {
                currentMessages = [];
                showWelcome();
            }
        }
    }
}

// Load Conversation
function loadConversation(id) {
    const conv = conversations.find(c => c.id === id);
    if (conv) {
        currentMessages = [...conv.messages];
        renderChat();
    }
}

// Show Welcome
function showWelcome() {
    document.getElementById('welcome').classList.remove('hidden');
    document.getElementById('chat').classList.add('hidden');
}

// Show Chat
function showChat() {
    document.getElementById('welcome').classList.add('hidden');
    document.getElementById('chat').classList.remove('hidden');
}

// Ask Example
function askExample(question) {
    document.getElementById('messageInput').value = question;
    sendMessage(new Event('submit'));
}

// Send Message
async function sendMessage(event) {
    event.preventDefault();

    if (isLoading) return;

    const input = document.getElementById('messageInput');
    const question = input.value.trim();

    if (!question) return;

    // Clear input
    input.value = '';

    // Show chat if hidden
    if (currentMessages.length === 0) {
        showChat();
    }

    // Add user message
    const userMessage = {
        role: 'user',
        content: question,
        timestamp: new Date().toISOString()
    };
    currentMessages.push(userMessage);
    renderChat();

    // Show loading
    isLoading = true;
    showLoading();
    disableInput();

    try {
        // Query API
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                top_k: 5,
                include_chunks: true
            })
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();

        // Add assistant message
        const assistantMessage = {
            role: 'assistant',
            content: data.answer,
            citations: data.citations,
            chunks: data.chunks,
            metadata: data.metadata,
            timestamp: new Date().toISOString()
        };
        currentMessages.push(assistantMessage);

    } catch (error) {
        console.error('Query error:', error);

        // Add error message
        const errorMessage = {
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date().toISOString()
        };
        currentMessages.push(errorMessage);
    } finally {
        isLoading = false;
        hideLoading();
        enableInput();
        renderChat();
    }
}

// Render Chat
function renderChat() {
    const chat = document.getElementById('chat');
    chat.innerHTML = currentMessages.map(msg => {
        if (msg.role === 'user') {
            return renderUserMessage(msg);
        } else {
            return renderAssistantMessage(msg);
        }
    }).join('');

    // Scroll to bottom
    setTimeout(() => {
        const messagesContainer = document.getElementById('messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Render User Message
function renderUserMessage(msg) {
    return `
        <div class="flex justify-end message">
            <div class="bg-indigo-600 text-white px-6 py-4 rounded-2xl max-w-2xl">
                <p class="whitespace-pre-wrap">${escapeHtml(msg.content)}</p>
            </div>
        </div>
    `;
}

// Remove citation numbers from text
function removeCitations(text) {
    return text.replace(/\s*\[(\d+)\]/g, '');
}

// Format assistant response with better styling
function formatResponse(text) {
    // Remove citations
    let formatted = removeCitations(text);

    // Convert **bold** to actual bold
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');

    // Convert numbered lists
    formatted = formatted.replace(/^(\d+)\.\s+\*\*(.+?)\*\*:\s*(.+?)$/gm,
        '<div class="mb-3"><span class="inline-flex items-center justify-center w-6 h-6 bg-indigo-600/20 text-indigo-400 rounded-full text-sm font-bold mr-2">$1</span><strong class="text-white">$2</strong>: <span class="text-slate-300">$3</span></div>');

    // Handle remaining numbered items
    formatted = formatted.replace(/^(\d+)\.\s+(.+?)$/gm,
        '<div class="mb-2 flex"><span class="inline-flex items-center justify-center w-6 h-6 bg-indigo-600/20 text-indigo-400 rounded-full text-sm font-bold mr-3 flex-shrink-0">$1</span><span class="text-slate-300 flex-1">$2</span></div>');

    return formatted;
}

// Render Assistant Message
function renderAssistantMessage(msg) {
    const formattedContent = formatResponse(msg.content);

    const citations = msg.citations && msg.citations.length > 0 ? `
        <div class="flex items-center gap-2 flex-wrap mt-4 pt-4 border-t border-slate-700">
            <span class="text-xs font-medium text-slate-400">
                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                </svg>
                Sources:
            </span>
            ${msg.citations.map(id => `
                <span class="inline-flex items-center px-2.5 py-1 bg-indigo-600/20 text-indigo-400 text-xs font-medium rounded-md hover:bg-indigo-600/30 transition-colors">
                    Ticket #${id}
                </span>
            `).join('')}
        </div>
    ` : '';

    const chunks = msg.chunks && msg.chunks.length > 0 ? `
        <details class="mt-4 pt-4 border-t border-slate-700">
            <summary class="text-sm font-medium text-indigo-400 cursor-pointer hover:text-indigo-300 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                View ${msg.chunks.length} source chunks
            </summary>
            <div class="mt-3 space-y-3">
                ${msg.chunks.map(chunk => `
                    <div class="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
                        <div class="flex items-start justify-between mb-2">
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="font-semibold text-sm text-white">Ticket #${chunk.ticket_id}</span>
                                    <span class="px-2 py-0.5 ${getScoreColor(chunk.score)} text-xs font-medium rounded">
                                        ${(chunk.score * 100).toFixed(1)}% match
                                    </span>
                                </div>
                                <div class="text-sm text-slate-300 font-medium">${escapeHtml(chunk.subject)}</div>
                            </div>
                        </div>
                        <div class="flex gap-2 flex-wrap mb-3">
                            ${chunk.product ? `<span class="px-2 py-1 bg-purple-600/20 text-purple-400 text-xs rounded">${chunk.product}</span>` : ''}
                            ${chunk.issue_type ? `<span class="px-2 py-1 bg-orange-600/20 text-orange-400 text-xs rounded">${chunk.issue_type}</span>` : ''}
                            ${chunk.priority ? `<span class="px-2 py-1 bg-red-600/20 text-red-400 text-xs rounded">${chunk.priority}</span>` : ''}
                            ${chunk.region ? `<span class="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded">${chunk.region}</span>` : ''}
                        </div>
                        <div class="text-sm text-slate-400 leading-relaxed">
                            ${escapeHtml(chunk.content.substring(0, 250))}${chunk.content.length > 250 ? '...' : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </details>
    ` : '';

    return `
        <div class="flex items-start gap-4 message">
            <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
            </div>
            <div class="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-3xl">
                <div class="prose prose-invert max-w-none">
                    <div class="text-slate-200 leading-relaxed">${formattedContent}</div>
                </div>
                ${citations}
                ${chunks}
            </div>
        </div>
    `;
}

// Show Loading
function showLoading() {
    const chat = document.getElementById('chat');
    const loadingHtml = `
        <div id="loading" class="flex items-start gap-4 message">
            <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-2xl px-6 py-4">
                <div class="loading-dots flex items-center gap-1">
                    <span class="w-2 h-2 bg-indigo-600 rounded-full"></span>
                    <span class="w-2 h-2 bg-indigo-600 rounded-full"></span>
                    <span class="w-2 h-2 bg-indigo-600 rounded-full"></span>
                </div>
            </div>
        </div>
    `;
    chat.insertAdjacentHTML('beforeend', loadingHtml);

    // Scroll to bottom
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Hide Loading
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.remove();
    }
}

// Disable Input
function disableInput() {
    document.getElementById('messageInput').disabled = true;
    document.getElementById('sendButton').disabled = true;
}

// Enable Input
function enableInput() {
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendButton').disabled = false;
    document.getElementById('messageInput').focus();
}

// Get Score Color
function getScoreColor(score) {
    if (score >= 0.7) return 'bg-green-600/20 text-green-400';
    if (score >= 0.5) return 'bg-yellow-600/20 text-yellow-400';
    return 'bg-red-600/20 text-red-400';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
