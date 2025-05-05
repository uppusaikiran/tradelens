/**
 * Chat Integration API for TradeLens
 * Provides reliable methods to interact with the chat interface
 */

// Global chat interface
const TradeLensChat = {
    initialized: false,
    initAttempts: 0,
    maxInitAttempts: 10,
    pollingInterval: null,
    observer: null,
    lastPromptTime: 0, // Track when the last prompt was sent
    
    /**
     * Initialize chat integration by setting up event listeners
     * and watching for dynamically loaded chat elements
     */
    init: function() {
        if (this.initialized) return;
        
        console.log('Chat integration initialization started');
        
        // Add event listeners to any chat prompt buttons on the page
        this.setupChatButtons();
        
        // Check if chat container already exists
        if (this.isAvailable()) {
            console.log('Chat container found immediately');
            this.markAsInitialized();
            return;
        }
        
        // Set up polling to find chat container when it becomes available
        this.startPolling();
        
        // Set up MutationObserver to detect when chat container is added to DOM
        this.setupObserver();
    },
    
    /**
     * Start polling for chat container
     */
    startPolling: function() {
        this.pollingInterval = setInterval(() => {
            this.initAttempts++;
            
            if (this.isAvailable()) {
                console.log('Chat container found after polling');
                this.markAsInitialized();
                this.stopPolling();
                return;
            }
            
            if (this.initAttempts >= this.maxInitAttempts) {
                console.warn(`Max polling attempts reached for chat container (${this.maxInitAttempts})`);
                this.stopPolling();
            }
        }, 500);
    },
    
    /**
     * Stop polling for chat container
     */
    stopPolling: function() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    },
    
    /**
     * Set up MutationObserver to detect when chat container is added to DOM
     */
    setupObserver: function() {
        if (!window.MutationObserver) return;
        
        this.observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length) {
                    if (this.isAvailable()) {
                        console.log('Chat container found via MutationObserver');
                        this.markAsInitialized();
                        this.disconnectObserver();
                        this.stopPolling();
                        return;
                    }
                }
            }
        });
        
        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    },
    
    /**
     * Disconnect MutationObserver
     */
    disconnectObserver: function() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    },
    
    /**
     * Mark chat integration as initialized
     */
    markAsInitialized: function() {
        this.initialized = true;
        console.log('Chat integration initialized successfully');
        
        // Setup any remaining event listeners
        this.setupChatButtons();
    },
    
    /**
     * Check if chat container is available
     */
    isAvailable: function() {
        const chatContainer = document.querySelector('.chat-bot-container');
        const available = chatContainer !== null;
        
        if (available) {
            console.log('Chat container is available');
            
            // Check if chat.js exposed its functions globally
            if (window.TradeLensChat && typeof window.TradeLensChat.addMessage === 'function') {
                console.log('Chat functions are available globally');
            } else {
                console.warn('Chat container found but functions not globally available');
            }
        }
        
        return available;
    },
    
    /**
     * Set up event listeners for chat prompt buttons
     */
    setupChatButtons: function() {
        const chatPromptButtons = document.querySelectorAll('[data-chat-prompt]');
        
        console.log(`Found ${chatPromptButtons.length} chat prompt buttons`);
        
        chatPromptButtons.forEach(button => {
            // Check if event listener is already attached
            if (button.dataset.chatListenerAdded) return;
            
            // Check if this is on the risk review page where we handle buttons differently
            const isRiskPage = window.location.pathname.includes('/risk-review');
            const isRiskButton = button.id === 'tariff-impact-btn';
            
            // Skip if this is a risk button on the risk page (handled separately)
            if (isRiskPage && isRiskButton) {
                console.log('Skipping risk review button as it has specialized handling');
                return;
            }
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Get prompt before potentially removing attribute
                const prompt = button.getAttribute('data-chat-prompt');
                
                // For risk buttons, remove attribute to prevent double handling
                if (isRiskButton) {
                    button.removeAttribute('data-chat-prompt');
                }
                
                if (prompt) {
                    console.log('Chat button clicked with prompt:', prompt);
                    this.sendPrompt(prompt);
                }
            });
            
            // Mark as having event listener attached
            button.dataset.chatListenerAdded = 'true';
            console.log('Added event listener to chat button:', button.textContent.trim());
        });
    },
    
    /**
     * Send a prompt to the chat interface
     * 
     * @param {string} prompt - The prompt to send
     * @returns {boolean} - Whether the prompt was successfully sent
     */
    sendPrompt: function(prompt) {
        if (!prompt) return false;
        
        // Debounce: prevent sending the same prompt multiple times in quick succession
        const now = Date.now();
        if (now - this.lastPromptTime < 1000) { // 1000ms debounce time
            console.log('Debounced prompt:', prompt);
            return false;
        }
        this.lastPromptTime = now;
        
        console.log('Attempting to send prompt:', prompt);
        
        // Look for the chat elements
        const chatContainer = document.querySelector('.chat-bot-container');
        if (!chatContainer) {
            console.error('Chat container not found');
            alert("Chat not available. Please try reloading the page.");
            return false;
        }
        
        // Make chat visible
        if (chatContainer.classList.contains('collapsed')) {
            console.log('Expanding collapsed chat container');
            chatContainer.classList.remove('collapsed');
        }
        
        // Use a direct API call approach to avoid duplicate submissions
        // This completely bypasses the chat.js system and ensures a single submission
        if (prompt.includes('tariff') || prompt.includes('risk')) {
            try {
                console.log('Using direct API call for risk/tariff prompt');
                
                // First, immediately add the user message to the chat
                if (window.TradeLensChat && typeof window.TradeLensChat.addMessage === 'function') {
                    // Add user message right away
                    window.TradeLensChat.addMessage('user', prompt);
                    
                    // Get the chat messages container
                    const chatMessages = document.querySelector('.chat-bot-messages');
                    if (!chatMessages) {
                        console.error('Chat messages container not found');
                        return false;
                    }
                    
                    // Add typing indicator
                    const typingIndicator = document.createElement('div');
                    typingIndicator.classList.add('chat-bot-message', 'bot', 'typing');
                    typingIndicator.innerHTML = '<div class="chat-bot-message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
                    chatMessages.appendChild(typingIndicator);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    
                    // Disable the input field while waiting for the response
                    const chatInput = document.querySelector('.chat-bot-input');
                    const sendButton = document.querySelector('.chat-bot-send');
                    if (chatInput) chatInput.disabled = true;
                    if (sendButton) sendButton.disabled = true;
                    
                    // Then make the API call after showing the user's message
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: prompt,
                            stock: null
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Remove typing indicator
                        if (typingIndicator.parentNode) {
                            chatMessages.removeChild(typingIndicator);
                        }
                        
                        // Add response if available
                        if (data.response) {
                            // Format the response
                            const formattedResponse = data.response
                                .replace(/\n\n/g, '<br><br>')
                                .replace(/\n/g, '<br>')
                                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
                            
                            // Add the bot message
                            window.TradeLensChat.addMessage('bot', formattedResponse, 
                                data.provider ? (data.provider + (data.model ? ` - ${data.model}` : '')) : null);
                        } else {
                            window.TradeLensChat.addMessage('bot', 'Sorry, I couldn\'t process your request.');
                        }
                        
                        // Re-enable the input field
                        if (chatInput) chatInput.disabled = false;
                        if (sendButton) sendButton.disabled = false;
                        if (chatInput) chatInput.focus();
                    })
                    .catch(error => {
                        console.error('Error fetching chat response:', error);
                        
                        // Remove typing indicator
                        if (typingIndicator.parentNode) {
                            chatMessages.removeChild(typingIndicator);
                        }
                        
                        // Add error message
                        window.TradeLensChat.addMessage('bot', 'Sorry, there was an error processing your request. Please try again.');
                        
                        // Re-enable the input field
                        if (chatInput) chatInput.disabled = false;
                        if (sendButton) sendButton.disabled = false;
                    });
                    
                    return true;
                }
            } catch (error) {
                console.error('Error with direct API call:', error);
                // Fall through to regular approaches
            }
        }
        
        // Try multiple approaches to send the message
        let success = false;
        
        // Approach 1: Use the chat.js exposed functions
        if (window.TradeLensChat && typeof window.TradeLensChat.addMessage === 'function') {
            try {
                console.log('Using TradeLensChat.addMessage function');
                // Add user message to chat
                window.TradeLensChat.addMessage('user', prompt);
                
                // Send the message to API
                if (typeof window.TradeLensChat.sendMessage === 'function') {
                    window.TradeLensChat.sendMessage(prompt);
                    success = true;
                } else if (typeof window.TradeLensChat.sendToAPI === 'function') {
                    window.TradeLensChat.sendToAPI(prompt);
                    success = true;
                }
            } catch (error) {
                console.error('Error using TradeLensChat functions:', error);
                // Continue to next approach if this fails
            }
        }
        
        // Approach 2: Use DOM manipulation if function approach failed
        if (!success) {
            try {
                console.log('Using DOM manipulation to send prompt');
                const chatInput = document.querySelector('.chat-bot-input');
                const sendButton = document.querySelector('.chat-bot-send');
                
                if (!chatInput || !sendButton) {
                    console.error('Could not find chat input or send button');
                    return false;
                }
                
                // Set the message in the input field
                chatInput.value = prompt;
                chatInput.focus();
                
                // Click the send button
                sendButton.click();
                success = true;
            } catch (error) {
                console.error('Error manipulating DOM to send prompt:', error);
            }
        }
        
        // Approach 3: Last resort - try triggering Enter key on input
        if (!success) {
            try {
                console.log('Using Enter key simulation as last resort');
                const chatInput = document.querySelector('.chat-bot-input');
                
                if (!chatInput) {
                    console.error('Could not find chat input');
                    return false;
                }
                
                // Set the message in the input field
                chatInput.value = prompt;
                chatInput.focus();
                
                // Simulate Enter keypress
                const enterEvent = new KeyboardEvent('keypress', {
                    key: 'Enter',
                    code: 'Enter',
                    which: 13,
                    keyCode: 13,
                    bubbles: true
                });
                
                chatInput.dispatchEvent(enterEvent);
                success = true;
            } catch (error) {
                console.error('Error simulating Enter key:', error);
            }
        }
        
        return success;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat integration
    TradeLensChat.init();
    
    // Expose to window for global access
    window.TradeLensChat = window.TradeLensChat || {};
    
    // Merge existing functions with our interface
    for (const key in TradeLensChat) {
        if (typeof TradeLensChat[key] === 'function' && !window.TradeLensChat[key]) {
            window.TradeLensChat[key] = TradeLensChat[key];
        }
    }
    
    console.log('Chat integration initialized and exposed globally');
}); 