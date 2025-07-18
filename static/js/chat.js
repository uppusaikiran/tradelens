/**
 * Common chat functionality for TradeLens
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing chat bot from common script');
    
    const chatBotContainer = document.querySelector('.chat-bot-container');
    const chatBotToggle = document.querySelector('.chat-bot-toggle');
    const chatBotClear = document.querySelector('.chat-bot-clear');
    const chatBotMessages = document.querySelector('.chat-bot-messages');
    const chatBotInput = document.querySelector('.chat-bot-input');
    const chatBotSend = document.querySelector('.chat-bot-send');
    const modelInfoBanner = document.getElementById('model-info-banner');
    let currentStock = document.getElementById('current-stock')?.value || null;
    
    // Debounce variables
    let lastMessageTime = 0;
    const DEBOUNCE_DELAY = 1000; // 1 second
    
    // If chat elements don't exist, exit early
    if (!chatBotContainer || !chatBotInput || !chatBotSend) {
        console.log('Chat components not found on this page');
        return;
    }
    
    console.log('Chat components found, initializing...');
    
    // Notify TradeLensChat that the chat bot is ready
    if (window.TradeLensChat && typeof window.TradeLensChat === 'object') {
        console.log('Notifying TradeLensChat that chat components are ready');
        window.TradeLensChat.isAvailable();
    }
    
    // Function to check server availability
    function checkServerAvailability() {
        console.log('Checking server availability...');
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: 'check_api',
                stock: currentStock
            }),
            // Short timeout for availability check
            signal: AbortSignal.timeout(5000)
        })
        .then(response => {
            if (!response.ok) {
                console.warn('Server responded but status not OK:', response.status);
                showServerOfflineMessage();
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.api_available) {
                console.log('Server is available, API status:', data);
                
                // Display model info banner
                updateModelInfoBanner(data.current_settings);
                
                // Add chat suggestions if API is available and on stock page
                if (currentStock) {
                    addChatSuggestions();
                }
            } else {
                console.warn('Server responded but API is not available');
                showApiUnavailableMessage();
            }
        })
        .catch(error => {
            console.error('Error checking server availability:', error);
            if (error.name === 'TimeoutError' || error.name === 'AbortError') {
                showServerOfflineMessage();
            } else {
                showApiUnavailableMessage();
            }
        });
    }
    
    // Function to show server offline message
    function showServerOfflineMessage() {
        addMessage('bot', 'The server appears to be offline or restarting. Please try again in a moment.');
    }
    
    // Function to show API unavailable message
    function showApiUnavailableMessage() {
        addMessage('bot', 'No AI provider is available. Please configure your API keys in the .env file.');
    }
    
    // Function to add chat suggestions
    function addChatSuggestions() {
        const suggestionMessage = document.createElement('div');
        suggestionMessage.classList.add('chat-bot-message', 'bot');
        
        const suggestionContent = document.createElement('div');
        suggestionContent.classList.add('chat-bot-message-content');
        suggestionContent.innerHTML = `
            <div class="chat-suggestions">
                <button class="chat-suggestion" data-text="Is it a good time to buy ${currentStock} based on my transaction history?">
                    Is it a good time to buy ${currentStock}?
                </button>
                <button class="chat-suggestion" data-text="Have I made impulse buys or panic sells with ${currentStock}?">
                    Analyze my trading patterns with ${currentStock}
                </button>
            </div>
        `;
        
        suggestionMessage.appendChild(suggestionContent);
        chatBotMessages.appendChild(suggestionMessage);
        
        // Add click event to suggestions
        document.querySelectorAll('.chat-suggestion').forEach(button => {
            button.addEventListener('click', () => {
                const text = button.dataset.text;
                chatBotInput.value = text;
                sendMessage();
            });
        });
        
        // Scroll to bottom
        chatBotMessages.scrollTop = chatBotMessages.scrollHeight;
    }
    
    // Call the API to check availability and get current settings
    checkServerAvailability();
    
    // Function to update model info banner
    function updateModelInfoBanner(settings) {
        if (!settings || !modelInfoBanner) return;
        
        let providerName, modelName, iconPath;
        
        if (settings.ai_provider === 'openai') {
            providerName = 'OpenAI';
            modelName = 'GPT-3.5 Turbo';
            iconPath = 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/512px-ChatGPT_logo.svg.png';
        } else {
            providerName = 'Perplexity';
            modelName = settings.perplexity_model || 'Default';
            iconPath = '/static/img/icons/perplexity_icon.png';
        }
        
        modelInfoBanner.innerHTML = `
            <img src="${iconPath}" alt="${providerName} Icon">
            <span>Powered by <strong>${providerName}</strong> — Model: <strong>${modelName}</strong></span>
            <a href="/settings">Change</a>
        `;
    }

    // Toggle chat bot visibility
    if (chatBotToggle) {
        chatBotToggle.addEventListener('click', () => {
            chatBotContainer.classList.toggle('collapsed');
        });
    }
    
    // Clear chat messages
    if (chatBotClear) {
        chatBotClear.addEventListener('click', () => {
            // Keep only the first message (welcome message) and the model info banner
            const welcomeMessage = chatBotMessages.firstElementChild;
            chatBotMessages.innerHTML = '';
            chatBotMessages.appendChild(welcomeMessage);
            if (modelInfoBanner) {
                chatBotMessages.appendChild(modelInfoBanner);
            }
        });
    }
    
    // Send button click event
    if (chatBotSend) {
        chatBotSend.addEventListener('click', sendMessage);
    }
    
    // Enter key event
    if (chatBotInput) {
        chatBotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    function sendMessage() {
        const message = chatBotInput.value.trim();
        if (!message) return;
        
        // Implement debouncing to prevent duplicate submissions
        const now = Date.now();
        if (now - lastMessageTime < DEBOUNCE_DELAY) {
            console.log('Message debounced to prevent duplicate submission');
            return;
        }
        lastMessageTime = now;
        
        // Check if the message already exists in the chat (to prevent duplicates)
        let isDuplicate = false;
        const existingMessages = document.querySelectorAll('.chat-bot-message.user .chat-bot-message-content');
        existingMessages.forEach(msgElement => {
            // Check if this message was just added (within the last second)
            const timestamp = parseInt(msgElement.dataset.timestamp || '0');
            if (msgElement.textContent.trim() === message && now - timestamp < 2000) {
                console.log('Preventing duplicate message submission');
                isDuplicate = true;
            }
        });
        
        if (isDuplicate) {
            // Clear the input but don't send the message again
            chatBotInput.value = '';
            return;
        }
        
        // Add user message to chat with timestamp
        const messageElement = addMessage('user', message);
        if (messageElement) {
            const contentElement = messageElement.querySelector('.chat-bot-message-content');
            if (contentElement) {
                contentElement.dataset.timestamp = String(now);
            }
        }
        
        chatBotInput.value = '';
        
        // Show typing indicator and send to API
        sendToAPI(message);
    }
    
    function addMessage(sender, text, modelInfo = null) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-bot-message', sender);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('chat-bot-message-content');
        
        // For bot messages with model info
        if (sender === 'bot') {
            // Check if the text is already HTML (already formatted) or needs formatting
            if (text.startsWith('<') && text.includes('</')) {
                // Already HTML formatted
                messageContent.innerHTML = text;
            } else if (typeof marked !== 'undefined') {
                // Use marked.js to parse markdown
                messageContent.innerHTML = marked.parse(text);
            } else {
                // Fallback to basic formatting if marked isn't available
                messageContent.innerHTML = text
                    .replace(/\n\n/g, '<br><br>')
                    .replace(/\n/g, '<br>')
                    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
            }
            
            // Add model info if provided
            if (modelInfo) {
                const modelInfoElement = document.createElement('div');
                modelInfoElement.classList.add('model-info');
                modelInfoElement.textContent = `Model: ${modelInfo}`;
                messageContent.appendChild(modelInfoElement);
            }
        } else {
            // Use textContent for user messages (for security)
            messageContent.textContent = text;
        }
        
        messageElement.appendChild(messageContent);
        chatBotMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatBotMessages.scrollTop = chatBotMessages.scrollHeight;
        
        return messageElement;
    }
    
    function sendToAPI(message) {
        // Check first if there's already a pending request for the same message
        const existingTypingIndicators = document.querySelectorAll('.chat-bot-message.typing');
        if (existingTypingIndicators.length > 0) {
            // There's already a request in progress, don't send another one
            console.log('Request already in progress, not sending duplicate');
            return;
        }
        
        // Create typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('chat-bot-message', 'bot', 'typing');
        typingIndicator.innerHTML = '<div class="chat-bot-message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
        chatBotMessages.appendChild(typingIndicator);
        
        // Disable input while waiting for response
        chatBotInput.disabled = true;
        if (chatBotSend) chatBotSend.disabled = true;
        
        // Get current stock symbol if available
        currentStock = document.getElementById('current-stock')?.value || null;
        
        // Set a timeout for the API call
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 60000); // 60 seconds timeout
        });
        
        // Create the fetch promise
        const fetchPromise = fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                stock: currentStock
            }),
        });
        
        // Race between fetch and timeout with retry functionality
        let retryCount = 0;
        const maxRetries = 2;
        
        function attemptFetch() {
            // Race between fetch and timeout
            Promise.race([fetchPromise, timeoutPromise])
                .then(response => {
                    if (!response.ok) {
                        // Handle HTTP error responses (400-599)
                        let errorMessage = `Server error: ${response.status}`;
                        console.error(errorMessage);
                        throw new Error(errorMessage);
                    }
                    return response.json();
                })
                .then(data => {
                    // Remove typing indicator
                    chatBotMessages.removeChild(typingIndicator);
                    
                    // Check if error was returned from server
                    if (data.error) {
                        throw new Error(`Server error: ${data.error}`);
                    }
                    
                    // Add response to chat
                    if (data.response) {
                        // Check if marked library is available
                        let formattedResponse;
                        if (typeof marked !== 'undefined') {
                            // Parse markdown using marked library
                            formattedResponse = marked.parse(data.response);
                        } else {
                            // Fallback to basic formatting if marked isn't available
                            formattedResponse = data.response
                                .replace(/\n\n/g, '<br><br>')
                                .replace(/\n/g, '<br>')
                                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
                        }
                        
                        // Create formatted response element
                        const messageElement = document.createElement('div');
                        messageElement.classList.add('chat-bot-message', 'bot');
                        
                        const messageContent = document.createElement('div');
                        messageContent.classList.add('chat-bot-message-content');
                        messageContent.innerHTML = formattedResponse;
                        
                        // Add model info if available
                        if (data.model || data.provider) {
                            const modelInfoElement = document.createElement('div');
                            modelInfoElement.classList.add('model-info');
                            
                            let modelText = '';
                            if (data.provider) {
                                modelText += data.provider;
                            }
                            if (data.model) {
                                if (modelText) modelText += ' - ';
                                modelText += data.model;
                            }
                            
                            modelInfoElement.textContent = modelText;
                            messageContent.appendChild(modelInfoElement);
                        }
                        
                        messageElement.appendChild(messageContent);
                        chatBotMessages.appendChild(messageElement);
                    } else {
                        addMessage('bot', 'Sorry, I couldn\'t process your request.');
                    }
                    
                    // Scroll to bottom
                    chatBotMessages.scrollTop = chatBotMessages.scrollHeight;
                    
                    // Re-enable input
                    chatBotInput.disabled = false;
                    if (chatBotSend) chatBotSend.disabled = false;
                    chatBotInput.focus();
                })
                .catch(error => {
                    console.error('Error sending message to API:', error);
                    
                    // Check if we should retry
                    if (retryCount < maxRetries && 
                        (error.message.includes('Failed to fetch') || 
                         error.message.includes('NetworkError') || 
                         error.message.includes('ERR_EMPTY_RESPONSE'))) {
                        
                        retryCount++;
                        console.log(`Retrying fetch (${retryCount}/${maxRetries})...`);
                        
                        // Let user know we're retrying
                        if (typingIndicator.parentNode) {
                            const retryText = document.createElement('span');
                            retryText.classList.add('retry-text');
                            retryText.textContent = ` Retrying (${retryCount}/${maxRetries})...`;
                            typingIndicator.querySelector('.chat-bot-message-content').appendChild(retryText);
                        }
                        
                        // Wait before retrying
                        setTimeout(() => {
                            attemptFetch();
                        }, 2000); // 2 second delay before retry
                        return;
                    }
                    
                    // No more retries or different error
                    // Remove typing indicator
                    if (typingIndicator.parentNode) {
                        chatBotMessages.removeChild(typingIndicator);
                    }
                    
                    // Show error message
                    const errorMessage = document.createElement('div');
                    errorMessage.classList.add('chat-bot-message', 'bot', 'error');
                    
                    // Provide a more helpful error message
                    let errorText = 'Sorry, there was an error processing your request. ';
                    if (error.message === 'Request timeout') {
                        errorText += 'The AI service is taking too long to respond. This could be due to high server load or a complex query. Please try a shorter or simpler question, or try again later.';
                        
                        // Add retry button for timeout errors
                        errorText += '<div class="retry-container"><button class="retry-button">Retry</button></div>';
                    } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch') || error.message.includes('ERR_EMPTY_RESPONSE')) {
                        errorText += 'There appears to be a network connectivity issue or the server is restarting. Please wait a moment and try again.';
                        
                        // Add retry button for network errors
                        errorText += '<div class="retry-container"><button class="retry-button">Retry</button></div>';
                    } else if (error.message.includes('Server error')) {
                        errorText += 'The server encountered an issue processing your request. Please try a different question or try again later.';
                        
                        // Add retry button for server errors too
                        errorText += '<div class="retry-container"><button class="retry-button">Retry</button></div>';
                    } else {
                        errorText += 'Please try again later.';
                    }
                    
                    errorMessage.innerHTML = `
                        <div class="chat-bot-message-content">
                            ${errorText}
                        </div>
                    `;
                    chatBotMessages.appendChild(errorMessage);
                    
                    // Add event listener to retry button if present
                    const retryButton = errorMessage.querySelector('.retry-button');
                    if (retryButton) {
                        retryButton.addEventListener('click', () => {
                            // Remove error message
                            chatBotMessages.removeChild(errorMessage);
                            // Retry sending the message
                            sendToAPI(message);
                        });
                    }
                    
                    // Re-enable input
                    chatBotInput.disabled = false;
                    if (chatBotSend) chatBotSend.disabled = false;
                });
        }
        
        // Start the fetch process
        attemptFetch();
    }
    
    // Remove error message when user starts typing
    if (chatBotInput) {
        chatBotInput.addEventListener('input', () => {
            const errorMessage = document.querySelector('.chat-bot-message.error');
            if (errorMessage) {
                chatBotMessages.removeChild(errorMessage);
            }
        });
    }
    
    // Make the chat functions globally available
    window.TradeLensChat = window.TradeLensChat || {};
    window.TradeLensChat.addMessage = addMessage;
    window.TradeLensChat.sendMessage = sendMessage;
}); 