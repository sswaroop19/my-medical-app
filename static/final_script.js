// Chat data structure
let chats = [];
let activeChat = null;
let webSearchEnabled = true;
let lastQuestion = ""; // Store last question for regenerate functionality

// Suggestions for autocomplete
const suggestions = [
    "What are the symptoms of PCOS?",
    "How is endometriosis diagnosed?",
    "What are the stages of pregnancy?",
    "How to manage menopause symptoms?",
    "What causes irregular periods?",
    "How to prepare for a gynecological exam?",
    "What are the common birth control options?",
    "What are the signs of breast cancer?",
    "How to perform a breast self-exam?",
    "What are the symptoms of UTI?"
];

// DOM elements
let chatContainer, welcomeScreen, chatHistory, questionInput, submitBtn, newChatBtn, 
    webSearchToggle, autocompleteContainer, suggestionCards, settingsBtn, settingsModal, 
    closeModalBtn, clearAllBtn, notification;

// Initialize
function init() {
    // Get DOM elements
    chatContainer = document.getElementById('chat-container');
    welcomeScreen = document.getElementById('welcome-screen');
    chatHistory = document.getElementById('chat-history');
    questionInput = document.getElementById('question-input');
    submitBtn = document.getElementById('submit-btn');
    newChatBtn = document.getElementById('new-chat-btn');
    webSearchToggle = document.getElementById('web-search-toggle');
    autocompleteContainer = document.getElementById('autocomplete-container');
    suggestionCards = document.querySelectorAll('.suggestion-card');
    settingsBtn = document.getElementById('settings-btn');
    settingsModal = document.getElementById('settings-modal');
    closeModalBtn = document.getElementById('close-modal');
    clearAllBtn = document.getElementById('clear-all-btn');
    notification = document.getElementById('notification');
    
    loadChats();
    setupEventListeners();
    
    // Auto-resize textarea
    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Show autocomplete suggestions
        showAutocomplete();
    });
}

// Load chats from localStorage
function loadChats() {
    const savedChats = localStorage.getItem('medicalChats');
    if (savedChats) {
        chats = JSON.parse(savedChats);
        renderChatHistory();
        
        // Load last active chat if exists
        const lastActiveId = localStorage.getItem('activeChat');
        if (lastActiveId) {
            const chat = chats.find(c => c.id === lastActiveId);
            if (chat) {
                loadChat(chat.id);
            }
        }
    }
    
    // Load web search setting
    const savedWebSearch = localStorage.getItem('webSearchEnabled');
    if (savedWebSearch !== null) {
        webSearchEnabled = savedWebSearch === 'true';
        webSearchToggle.checked = webSearchEnabled;
    }
}

// Save chats to localStorage
function saveChats() {
    localStorage.setItem('medicalChats', JSON.stringify(chats));
    if (activeChat) {
        localStorage.setItem('activeChat', activeChat.id);
    }
}

// Create a new chat
function createNewChat() {
    const chatId = Date.now().toString();
    const newChat = {
        id: chatId,
        title: 'New Chat',
        messages: []
    };
    
    chats.unshift(newChat); // Add to beginning of array
    saveChats();
    renderChatHistory();
    loadChat(chatId);
    
    // Show welcome screen with suggestions
    welcomeScreen.style.display = 'flex';
    
    // Add header for new chat (only one header)
    chatContainer.innerHTML = '';
    const headerDiv = document.createElement('div');
    headerDiv.className = 'chat-header';
    headerDiv.innerHTML = `
        <h1>New Conversation</h1>
        <p>Start a new conversation with Medical Assistant</p>
    `;
    chatContainer.appendChild(headerDiv);
    chatContainer.appendChild(welcomeScreen);
    
    questionInput.focus();
}

// Load a specific chat
function loadChat(chatId) {
    activeChat = chats.find(chat => chat.id === chatId);
    
    if (!activeChat) return;
    
    // Update UI
    chatContainer.innerHTML = '';
    
    // Add header for the chat (only one header)
    const headerDiv = document.createElement('div');
    headerDiv.className = 'chat-header';
    headerDiv.innerHTML = `
        <h1>${activeChat.title}</h1>
        <p>Conversation with Medical Assistant</p>
    `;
    chatContainer.appendChild(headerDiv);
    
    // Mark active chat in sidebar
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    const chatItem = document.querySelector(`.chat-item[data-id="${chatId}"]`);
    if (chatItem) chatItem.classList.add('active');
    
    // Show welcome screen if no messages
    if (activeChat.messages.length === 0) {
        chatContainer.appendChild(welcomeScreen);
    } else {
        // Render messages
        activeChat.messages.forEach(message => {
            renderMessage(message.role, message.content, message.sources, message.title);
        });
    }
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Render chat history in sidebar
function renderChatHistory() {
    chatHistory.innerHTML = '';
    
    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item';
        chatItem.dataset.id = chat.id;
        if (activeChat && chat.id === activeChat.id) {
            chatItem.classList.add('active');
        }
        
        chatItem.innerHTML = `
            <span class="chat-icon">💬</span>
            <span class="chat-title">${chat.title}</span>
        `;
        
        chatItem.addEventListener('click', () => loadChat(chat.id));
        chatHistory.appendChild(chatItem);
    });
}

// Generate a title for the response based on the question
function generateTitle(question) {
    // Extract main topic from question
    let title = question.trim();
    
    // Remove question words
    title = title.replace(/^(what|how|why|when|where|who|is|are|can|could|should|would|do|does|did|will)\s+/i, '');
    
    // Capitalize first letter
    title = title.charAt(0).toUpperCase() + title.slice(1);
    
    // Limit length
    if (title.length > 50) {
        title = title.substring(0, 47) + '...';
    }
    
    // Add a period if needed
    if (!title.endsWith('.') && !title.endsWith('?') && !title.endsWith('!')) {
        title += '.';
    }
    
    return title;
}

// Render a message in the chat
function renderMessage(role, content, sources = null, title = null) {
    // Hide welcome screen if visible
    if (welcomeScreen.parentNode === chatContainer) {
        chatContainer.removeChild(welcomeScreen);
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    
    const messageRole = document.createElement('div');
    messageRole.className = 'message-role';
    
    // Add role icon
    const roleIcon = document.createElement('div');
    roleIcon.className = `message-role-icon ${role}-icon`;
    roleIcon.textContent = role === 'user' ? 'U' : 'A';
    messageRole.appendChild(roleIcon);
    
    messageRole.appendChild(document.createTextNode(role === 'user' ? 'You' : 'Medical Assistant'));
    messageHeader.appendChild(messageRole);
    
    // Add action buttons for assistant messages
    if (role === 'assistant') {
        const messageActions = document.createElement('div');
        messageActions.className = 'message-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn copy-btn';
        copyBtn.title = 'Copy to clipboard';
        copyBtn.innerHTML = '<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>';
        copyBtn.onclick = function() {
            copyToClipboard(content);
            return false;
        };
        messageActions.appendChild(copyBtn);
        
        const regenerateBtn = document.createElement('button');
        regenerateBtn.className = 'action-btn regenerate-btn';
        regenerateBtn.title = 'Regenerate response';
        regenerateBtn.innerHTML = '<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>';
        regenerateBtn.onclick = function() {
            regenerateResponse();
            return false;
        };
        messageActions.appendChild(regenerateBtn);
        
        messageHeader.appendChild(messageActions);
    }
    
    messageDiv.appendChild(messageHeader);
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Process content
    if (role === 'assistant') {
        // Add title if available or generate one
        if (!title && lastQuestion) {
            title = generateTitle(lastQuestion);
        }
        
        if (title) {
            const messageTitle = document.createElement('div');
            messageTitle.className = 'message-title';
            messageTitle.textContent = title;
            messageContent.appendChild(messageTitle);
        }
        
        // Convert markdown-like syntax
        let processedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        
        // Create a div for the actual content
        const contentDiv = document.createElement('div');
        contentDiv.innerHTML = processedContent;
        messageContent.appendChild(contentDiv);
        
        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesContainer = document.createElement('div');
            sourcesContainer.className = 'sources-container';
            
            const sourcesTitle = document.createElement('div');
            sourcesTitle.className = 'sources-title';
            sourcesTitle.textContent = 'Sources:';
            sourcesContainer.appendChild(sourcesTitle);
            
            sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                
                // Check if it's a web search result with an image
                if (source.includes('Web Search Result') && source.includes('[img:')) {
                    const match = source.match(/\[(\d+)\] Web Search Result #\d+: (.*?) \((https?:\/\/[^\s\)]+)\) \[img:(https?:\/\/[^\s\]]+)\]/);
                    if (match) {
                        const [_, num, title, url, img] = match;
                        sourceItem.innerHTML = `
                            <div class="web-result">
                                <div class="web-result-image">
                                    <img src="${img}" alt="${title}" onerror="this.style.display='none'">
                                </div>
                                <div class="web-result-content">
                                    <a href="${url}" target="_blank" class="web-result-title">${title}</a>
                                    <div class="web-result-citation">[${num}] ${url}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        sourceItem.textContent = source;
                    }
                } else {
                    sourceItem.textContent = source;
                }
                
                sourcesContainer.appendChild(sourceItem);
            });
            
            messageContent.appendChild(sourcesContainer);
        }
    } else {
        messageContent.textContent = content;
        // Store last question for regenerate functionality
        lastQuestion = content;
    }
    
    messageDiv.appendChild(messageContent);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Copy text to clipboard with notification
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard');
    }).catch(err => {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy');
    });
}

// Show notification
function showNotification(message) {
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 2000);
}

// Regenerate response
function regenerateResponse() {
    if (!lastQuestion || !activeChat) return;
    
    // Remove the last assistant message
    if (activeChat.messages.length > 0 && activeChat.messages[activeChat.messages.length - 1].role === 'assistant') {
        activeChat.messages.pop();
        
        // Remove the last message from the UI
        const lastMessage = chatContainer.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('assistant-message')) {
            chatContainer.removeChild(lastMessage);
        }
        
        // Save chats
        saveChats();
        
        // Ask the question again
        askQuestion(lastQuestion);
    }
}

// Show autocomplete suggestions
function showAutocomplete() {
    const input = questionInput.value.trim().toLowerCase();
    
    if (input.length < 2) {
        autocompleteContainer.style.display = 'none';
        return;
    }
    
    // Filter suggestions
    const matchingSuggestions = suggestions.filter(suggestion => 
        suggestion.toLowerCase().includes(input)
    );
    
    if (matchingSuggestions.length === 0) {
        autocompleteContainer.style.display = 'none';
        return;
    }
    
    // Display suggestions
    autocompleteContainer.innerHTML = '';
    matchingSuggestions.slice(0, 5).forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.textContent = suggestion;
        item.onclick = () => {
            questionInput.value = suggestion;
            autocompleteContainer.style.display = 'none';
            questionInput.focus();
        };
        autocompleteContainer.appendChild(item);
    });
    
    autocompleteContainer.style.display = 'block';
}

// Send a question to the server
function askQuestion(question) {
    if (!activeChat) {
        createNewChat();
    }
    
    // Add user message
    renderMessage('user', question);
    
    // Add to chat data
    activeChat.messages.push({
        role: 'user',
        content: question
    });
    
    // Update chat title if it's the first message
    if (activeChat.messages.length === 1) {
        activeChat.title = question.substring(0, 30) + (question.length > 30 ? '...' : '');
        renderChatHistory();
    }
    
    // Save chats
    saveChats();
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="message-header">
            <div class="message-role">
                <div class="message-role-icon assistant-icon">A</div>
                Medical Assistant
            </div>
        </div>
        <div class="message-content">
            <div class="loading-spinner"></div> Thinking...
        </div>
    `;
    chatContainer.appendChild(loadingDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Disable input while processing
    questionInput.disabled = true;
    submitBtn.disabled = true;
    
    // Send question to server
    fetch('/api/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        },
        body: JSON.stringify({
            question: question,
            web_search_enabled: webSearchEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        chatContainer.removeChild(loadingDiv);
        
        if (data.error) {
            // Show error message
            renderMessage('assistant', `Error: ${data.error}`);
            
            // Add to chat data
            activeChat.messages.push({
                role: 'assistant',
                content: `Error: ${data.error}`
            });
        } else {
            // Generate title
            const title = generateTitle(question);
            
            // Show answer with sources
            renderMessage('assistant', data.answer, data.sources, title);
            
            // Add to chat data
            activeChat.messages.push({
                role: 'assistant',
                content: data.answer,
                sources: data.sources,
                title: title
            });
        }
        
        // Save chats
        saveChats();
        
        // Re-enable input
        questionInput.disabled = false;
        submitBtn.disabled = false;
        questionInput.focus();
    })
    .catch(error => {
        // Remove loading indicator
        chatContainer.removeChild(loadingDiv);
        
        // Show error message
        renderMessage('assistant', `Error: ${error.message}`);
        
        // Add to chat data
        activeChat.messages.push({
            role: 'assistant',
            content: `Error: ${error.message}`
        });
        
        // Save chats
        saveChats();
        
        // Re-enable input
        questionInput.disabled = false;
        submitBtn.disabled = false;
        questionInput.focus();
    });
}

// Clear all conversations
function clearAllConversations() {
    chats = [];
    activeChat = null;
    localStorage.removeItem('medicalChats');
    localStorage.removeItem('activeChat');
    renderChatHistory();
    createNewChat();
    closeModal();
    showNotification('All conversations cleared');
}

// Open settings modal
function openModal() {
    settingsModal.style.display = 'flex';
}

// Close settings modal
function closeModal() {
    settingsModal.style.display = 'none';
}

// Setup event listeners
function setupEventListeners() {
    // Submit question
    submitBtn.addEventListener('click', () => {
        const question = questionInput.value.trim();
        if (question) {
            askQuestion(question);
            questionInput.value = '';
            questionInput.style.height = 'auto';
            autocompleteContainer.style.display = 'none';
        }
    });
    
    // Submit on Enter (but allow Shift+Enter for new lines)
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitBtn.click();
        }
    });
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!autocompleteContainer.contains(e.target) && e.target !== questionInput) {
            autocompleteContainer.style.display = 'none';
        }
    });
    
    // New chat button
    newChatBtn.addEventListener('click', createNewChat);
    
    // Web search toggle
    webSearchToggle.addEventListener('change', function() {
        webSearchEnabled = webSearchToggle.checked;
        localStorage.setItem('webSearchEnabled', webSearchEnabled);
        showNotification(webSearchEnabled ? "Web search enabled" : "Web search disabled");
    });
    
    // Settings modal
    settingsBtn.addEventListener('click', openModal);
    closeModalBtn.addEventListener('click', closeModal);
    
    // Clear conversations button
    clearAllBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all conversations?')) {
            clearAllConversations();
        }
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeModal();
        }
    });
    
    // Suggestion cards
    suggestionCards.forEach(card => {
        card.addEventListener('click', () => {
            const question = card.querySelector('.suggestion-text').textContent;
            questionInput.value = question;
            submitBtn.click();
        });
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);