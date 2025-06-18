// PDF Tabs Management

// Store active PDF tabs
let activePdfTabs = {};
let currentPdfTab = null;

// Initialize PDF tabs
function initPdfTabs() {
    // Create tabs container if it doesn't exist
    if (!document.getElementById('pdf-tabs-container')) {
        const tabsContainer = document.createElement('div');
        tabsContainer.id = 'pdf-tabs-container';
        tabsContainer.className = 'pdf-tabs-container';
        tabsContainer.style.width = '100%';
        
        // Insert after the main chat container
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            // Insert after the chat container
            if (chatContainer.nextSibling) {
                chatContainer.parentNode.insertBefore(tabsContainer, chatContainer.nextSibling);
            } else {
                chatContainer.parentNode.appendChild(tabsContainer);
            }
        } else {
            // If chat container not found, append to main content
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.appendChild(tabsContainer);
            } else {
                // Last resort - append to body
                document.body.appendChild(tabsContainer);
            }
        }
        
        // Create tab header
        const tabHeader = document.createElement('div');
        tabHeader.className = 'pdf-tabs-header';
        tabsContainer.appendChild(tabHeader);
        
        // Create tab content area
        const tabContent = document.createElement('div');
        tabContent.className = 'pdf-tabs-content';
        tabsContainer.appendChild(tabContent);
        
        console.log('PDF tabs container created');
    }
    
    // Load saved PDF tabs from localStorage
    loadPdfTabsFromLocalStorage();
}

// Create a new PDF tab
function createPdfTab(pdfId, filename, pageCount) {
    // Check if tab already exists
    if (activePdfTabs[pdfId]) {
        setActivePdfTab(pdfId);
        return;
    }
    
    // Make sure the tabs container exists
    if (!document.getElementById('pdf-tabs-container')) {
        initPdfTabs();
    }
    
    // Show the tabs container
    const tabsContainer = document.getElementById('pdf-tabs-container');
    tabsContainer.style.display = 'block';
    
    // Create tab button
    const tabHeader = document.querySelector('.pdf-tabs-header');
    if (!tabHeader) {
        console.error('Tab header not found');
        return;
    }
    
    const tabButton = document.createElement('button');
    tabButton.className = 'pdf-tab-button';
    tabButton.setAttribute('data-pdf-id', pdfId);
    
    // Truncate filename if too long
    const displayName = filename.length > 20 ? filename.substring(0, 17) + '...' : filename;
    tabButton.textContent = displayName;
    
    // Add close button
    const closeButton = document.createElement('span');
    closeButton.className = 'pdf-tab-close';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = function(e) {
        e.stopPropagation();
        closePdfTab(pdfId);
    };
    tabButton.appendChild(closeButton);
    
    // Tab button click handler
    tabButton.onclick = function() {
        setActivePdfTab(pdfId);
    };
    
    tabHeader.appendChild(tabButton);
    
    // Create tab content
    const tabContent = document.querySelector('.pdf-tabs-content');
    
    // Use the template to create tab content
    fetch('/api/pdf-tab-template/' + pdfId)
        .then(response => response.text())
        .then(html => {
            const tabPane = document.createElement('div');
            tabPane.className = 'pdf-tab-pane';
            tabPane.setAttribute('data-pdf-id', pdfId);
            tabPane.innerHTML = html;
            tabContent.appendChild(tabPane);
            
            // Set up event handlers for the new tab
            setupPdfTabEventHandlers(tabPane, pdfId);
            
            // Store tab info
            activePdfTabs[pdfId] = {
                id: pdfId,
                filename: filename,
                pageCount: pageCount,
                messages: []
            };
            
            // Save to localStorage
            savePdfTabsToLocalStorage();
            
            // Set as active tab
            setActivePdfTab(pdfId);
        })
        .catch(error => {
            console.error('Error loading PDF tab template:', error);
            
            // Fallback to creating tab content manually
            const tabPane = document.createElement('div');
            tabPane.className = 'pdf-tab-pane';
            tabPane.setAttribute('data-pdf-id', pdfId);
            
            const pdfHeader = document.createElement('div');
            pdfHeader.className = 'pdf-header';
            
            const pdfTitle = document.createElement('h3');
            pdfTitle.textContent = filename;
            pdfHeader.appendChild(pdfTitle);
            
            const pdfPages = document.createElement('span');
            pdfPages.className = 'pdf-pages';
            pdfPages.textContent = pageCount + ' pages';
            pdfHeader.appendChild(pdfPages);
            
            tabPane.appendChild(pdfHeader);
            
            const chatContainer = document.createElement('div');
            chatContainer.className = 'pdf-chat-container';
            tabPane.appendChild(chatContainer);
            
            const inputContainer = document.createElement('div');
            inputContainer.className = 'pdf-input-container';
            
            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'input-wrapper';
            
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'pdf-question-input';
            input.placeholder = 'Ask a question about this PDF...';
            inputWrapper.appendChild(input);
            
            const button = document.createElement('button');
            button.className = 'pdf-submit-btn';
            button.textContent = 'Ask';
            inputWrapper.appendChild(button);
            
            inputContainer.appendChild(inputWrapper);
            tabPane.appendChild(inputContainer);
            
            tabContent.appendChild(tabPane);
            
            // Set up event handlers
            setupPdfTabEventHandlers(tabPane, pdfId);
            
            // Store tab info
            activePdfTabs[pdfId] = {
                id: pdfId,
                filename: filename,
                pageCount: pageCount,
                messages: []
            };
            
            // Save to localStorage
            savePdfTabsToLocalStorage();
            
            // Set as active tab
            setActivePdfTab(pdfId);
        });
}

// Set up event handlers for a PDF tab
function setupPdfTabEventHandlers(tabPane, pdfId) {
    const input = tabPane.querySelector('.pdf-question-input');
    const button = tabPane.querySelector('.pdf-submit-btn');
    
    // Submit question when button is clicked
    button.onclick = function() {
        const question = input.value.trim();
        if (question) {
            askPdfQuestion(pdfId, question);
            input.value = '';
        }
    };
    
    // Submit question when Enter key is pressed
    input.onkeypress = function(e) {
        if (e.key === 'Enter') {
            const question = input.value.trim();
            if (question) {
                askPdfQuestion(pdfId, question);
                input.value = '';
            }
        }
    };
}

// Ask a question about a specific PDF
function askPdfQuestion(pdfId, question) {
    // Add user message to chat
    addPdfMessage(pdfId, 'user', question);
    
    // Show loading indicator
    const chatContainer = document.querySelector(`.pdf-tab-pane[data-pdf-id="${pdfId}"] .pdf-chat-container`);
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message-loading';
    loadingDiv.innerHTML = '<div class="loading-spinner"></div><div class="loading-text">Thinking...</div>';
    chatContainer.appendChild(loadingDiv);
    
    // Send question to server
    fetch(`/api/ask-pdf/${pdfId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        chatContainer.removeChild(loadingDiv);
        
        if (data.error) {
            // Show error message
            addPdfMessage(pdfId, 'assistant', `Error: ${data.error}`);
        } else {
            // Show answer
            addPdfMessage(pdfId, 'assistant', data.answer);
        }
    })
    .catch(error => {
        // Remove loading indicator
        chatContainer.removeChild(loadingDiv);
        
        // Show error message
        addPdfMessage(pdfId, 'assistant', `Error: ${error.message}`);
    });
}

// Add a message to a PDF chat
function addPdfMessage(pdfId, role, content) {
    // Create message element
    const chatContainer = document.querySelector(`.pdf-tab-pane[data-pdf-id="${pdfId}"] .pdf-chat-container`);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = role === 'user' ? content : marked.parse(content);
    
    messageDiv.appendChild(messageContent);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Store message in memory
    if (activePdfTabs[pdfId]) {
        activePdfTabs[pdfId].messages.push({
            role: role,
            content: content
        });
        
        // Save to localStorage
        savePdfTabsToLocalStorage();
    }
}

// Set the active PDF tab
function setActivePdfTab(pdfId) {
    // Update current tab
    currentPdfTab = pdfId;
    
    // Make sure the tabs container is visible
    const tabsContainer = document.getElementById('pdf-tabs-container');
    if (tabsContainer) {
        tabsContainer.style.display = 'block';
    }
    
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.pdf-tab-button');
    tabButtons.forEach(button => {
        if (button.getAttribute('data-pdf-id') === pdfId) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Update tab panes
    const tabPanes = document.querySelectorAll('.pdf-tab-pane');
    tabPanes.forEach(pane => {
        if (pane.getAttribute('data-pdf-id') === pdfId) {
            pane.classList.add('active');
            pane.style.display = 'block';
        } else {
            pane.classList.remove('active');
            pane.style.display = 'none';
        }
    });
    
    // Scroll the active tab button into view
    const activeButton = document.querySelector(`.pdf-tab-button[data-pdf-id="${pdfId}"]`);
    if (activeButton) {
        activeButton.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
    
    // Show tabs container if there are active tabs
    if (Object.keys(activePdfTabs).length > 0) {
        if (tabsContainer) tabsContainer.style.display = 'block';
    } else {
        if (tabsContainer) tabsContainer.style.display = 'none';
    }
    
    console.log(`Activated tab: ${pdfId}`);
}

// Close a PDF tab
function closePdfTab(pdfId) {
    // Remove tab button
    const tabButton = document.querySelector(`.pdf-tab-button[data-pdf-id="${pdfId}"]`);
    if (tabButton) {
        tabButton.parentNode.removeChild(tabButton);
    }
    
    // Remove tab pane
    const tabPane = document.querySelector(`.pdf-tab-pane[data-pdf-id="${pdfId}"]`);
    if (tabPane) {
        tabPane.parentNode.removeChild(tabPane);
    }
    
    // Remove from active tabs
    delete activePdfTabs[pdfId];
    
    // Save to localStorage
    savePdfTabsToLocalStorage();
    
    // Set another tab as active if available
    const remainingTabs = Object.keys(activePdfTabs);
    if (remainingTabs.length > 0) {
        setActivePdfTab(remainingTabs[0]);
    } else {
        // Hide tabs container if no tabs left
        const tabsContainer = document.getElementById('pdf-tabs-container');
        tabsContainer.style.display = 'none';
        currentPdfTab = null;
    }
}

// Save PDF tabs to localStorage
function savePdfTabsToLocalStorage() {
    localStorage.setItem('pdfTabs', JSON.stringify(activePdfTabs));
}

// Load PDF tabs from localStorage
function loadPdfTabsFromLocalStorage() {
    const savedTabs = localStorage.getItem('pdfTabs');
    if (savedTabs) {
        const tabs = JSON.parse(savedTabs);
        
        // Create tabs
        Object.values(tabs).forEach(tab => {
            createPdfTab(tab.id, tab.filename, tab.pageCount);
            
            // Restore messages
            if (tab.messages && tab.messages.length > 0) {
                setTimeout(() => {
                    tab.messages.forEach(message => {
                        addPdfMessage(tab.id, message.role, message.content);
                    });
                }, 500); // Delay to ensure tab is created
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initPdfTabs();
    
    // Set up PDF upload form
    const pdfUploadForm = document.getElementById('pdf-upload-form');
    if (pdfUploadForm) {
        pdfUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('pdf-file');
            if (fileInput.files.length === 0) {
                alert('Please select a PDF file to upload');
                return;
            }
            
            const file = fileInput.files[0];
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please select a PDF file');
                return;
            }
            
            // Show loading indicator
            const uploadButton = document.getElementById('pdf-upload-button');
            const originalText = uploadButton.textContent;
            uploadButton.disabled = true;
            uploadButton.textContent = 'Uploading...';
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            
            // Upload file
            fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Reset form
                pdfUploadForm.reset();
                uploadButton.disabled = false;
                uploadButton.textContent = originalText;
                
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    // Create new tab for the PDF
                    createPdfTab(data.pdf_id, data.filename, data.page_count);
                }
            })
            .catch(error => {
                // Reset form
                pdfUploadForm.reset();
                uploadButton.disabled = false;
                uploadButton.textContent = originalText;
                
                alert(`Error: ${error.message}`);
            });
        });
    }
});