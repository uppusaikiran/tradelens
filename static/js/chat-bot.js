document.addEventListener('DOMContentLoaded', function() {
    const chatBotContainer = document.querySelector('.chat-bot-container');
    const chatBotToggle = document.querySelector('.chat-bot-toggle');
    const chatBotClear = document.querySelector('.chat-bot-clear');
    const chatBotMessages = document.querySelector('.chat-bot-messages');
    const chatBotInput = document.querySelector('.chat-bot-input');
    const chatBotSend = document.querySelector('.chat-bot-send');
    const aiBadge = document.getElementById('ai-badge');
    const modelInfoBanner = document.getElementById('model-info-banner');
    const modelProviderIcon = document.getElementById('model-provider-icon');
    const modelInfoText = document.getElementById('model-info-text');
    
    // Get paths from hidden fields
    const perplexityIconPath = document.getElementById('perplexity-icon-path')?.value || '/static/perplexity_icon.svg';
    const chatIconPath = document.getElementById('chat-icon-path')?.value || '/static/chat-icon.svg';
    const openaiIconPath = document.getElementById('openai-icon-path')?.value || 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/512px-ChatGPT_logo.svg.png';
    
    // Check if we're on a stock detail page
    const currentFilter = document.getElementById('currentFilter');
    const currentStock = currentFilter ? currentFilter.value : null;
    
    // Check if AI APIs are available
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: 'check_api' }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.api_available === false) {
            aiBadge.style.display = 'none';
            modelInfoBanner.style.display = 'none';
            addMessage("I'm operating in basic mode. For full AI capabilities, configure an OpenAI or Perplexity API key.", 'bot');
        } else {
            // Get provider and model information
            const settings = data.current_settings || { ai_provider: 'unknown', perplexity_model: 'unknown' };
            let providerName = 'AI';
            let modelName = 'Unknown';
            let iconPath = '';
            
            if (settings.ai_provider === 'openai') {
                providerName = 'OpenAI';
                modelName = 'GPT-3.5 Turbo';
                iconPath = openaiIconPath;
                aiBadge.textContent = 'OpenAI Powered';
                aiBadge.setAttribute('data-provider', 'openai');
            } else if (settings.ai_provider === 'perplexity') {
                providerName = 'Perplexity';
                modelName = settings.perplexity_model || 'sonar';
                // Use the path from hidden field
                iconPath = perplexityIconPath;
                aiBadge.textContent = 'Perplexity Powered';
                aiBadge.setAttribute('data-provider', 'perplexity');
            }
            
            // Update model info banner
            modelProviderIcon.src = iconPath;
            modelInfoText.innerHTML = `Powered by <strong>${providerName}</strong> — Model: <strong>${modelName}</strong>`;
            
            // Add stock-specific suggestions if on stock detail page
            if (currentStock && data.api_available) {
                setTimeout(() => {
                    const suggestionMessage = document.createElement('div');
                    suggestionMessage.classList.add('chat-bot-message', 'bot');
                    
                    const suggestionContent = document.createElement('div');
                    suggestionContent.classList.add('chat-bot-message-content');
                    suggestionContent.innerHTML = `
                        <p><strong>${currentStock} Analysis</strong> - Ask me about:</p>
                        <div class="chat-suggestions">
                            <button class="chat-suggestion" data-text="Is it a good time to buy ${currentStock} based on my transaction history?">
                                <span>📈 Is it a good time to buy?</span>
                            </button>
                            <button class="chat-suggestion" data-text="Have I made impulse buys or panic sells with ${currentStock}?">
                                <span>🧠 Analyze my trading pattern</span>
                            </button>
                        </div>
                    `;
                    
                    suggestionMessage.appendChild(suggestionContent);
                    chatBotMessages.appendChild(suggestionMessage);
                    
                    // Add event listeners for suggestion buttons
                    document.querySelectorAll('.chat-suggestion').forEach(button => {
                        button.addEventListener('click', function() {
                            const text = this.getAttribute('data-text');
                            chatBotInput.value = text;
                            sendMessage();
                        });
                    });
                    
                    // Scroll to bottom
                    chatBotMessages.scrollTop = chatBotMessages.scrollHeight;
                }, 1000);
            }
        }
    })
    .catch(error => {
        aiBadge.style.display = 'none';
        modelInfoBanner.style.display = 'none';
        console.error('Error checking API:', error);
    });
    
    // Toggle chat bot visibility
    chatBotToggle.addEventListener('click', () => {
        chatBotContainer.classList.toggle('collapsed');
    });
    
    // Clear chat messages
    chatBotClear.addEventListener('click', () => {
        // Keep only the first welcome message and model info banner
        const welcomeMessage = chatBotMessages.firstElementChild;
        const modelInfoBanner = document.getElementById('model-info-banner');
        
        // Remove modelInfoBanner from current location if present
        if (modelInfoBanner && modelInfoBanner.parentNode) {
            modelInfoBanner.parentNode.removeChild(modelInfoBanner);
        }
        
        // Clear messages and add welcome + model info
        chatBotMessages.innerHTML = '';
        chatBotMessages.appendChild(welcomeMessage);
        
        // Add model info banner back
        if (modelInfoBanner) {
            chatBotMessages.appendChild(modelInfoBanner);
        }
    });
    
    // Send message on button click
    chatBotSend.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    chatBotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    function sendMessage() {
        const message = chatBotInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        chatBotInput.value = '';
        
        // Process the message and get a response
        processMessage(message);
    }
    
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-bot-message', sender);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('chat-bot-message-content');
        
        // Process content based on sender
        if (sender === 'bot') {
            // Format message to handle newlines and parse markdown
            message = message.replace(/\n/g, '<br>');
            
            // Make URLs clickable
            message = message.replace(
                /(https?:\/\/[^\s]+)/g, 
                '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
            );
            
            messageContent.innerHTML = message;
        } else {
            messageContent.textContent = message;
        }
        
        messageElement.appendChild(messageContent);
        chatBotMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatBotMessages.scrollTop = chatBotMessages.scrollHeight;
    }
    
    function processMessage(message) {
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('chat-bot-message', 'bot', 'typing');
        typingIndicator.innerHTML = '<div class="chat-bot-message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
        chatBotMessages.appendChild(typingIndicator);
        
        // Disable input while processing
        chatBotInput.disabled = true;
        chatBotSend.disabled = true;
        
        // Check if we're on a stock detail page
        const currentFilter = document.getElementById('currentFilter');
        const currentStock = currentFilter ? currentFilter.value : null;
        
        // Make API call to get bot response
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                stock: currentStock
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            chatBotMessages.removeChild(typingIndicator);
            
            // Add response to chat
            if (!data.response) {
                throw new Error('Empty response received');
            }
            
            // Add the response to the chat
            addMessage(data.response, 'bot');
            
            // Update model info if provider information is available
            if (data.provider && data.model) {
                let providerName = data.provider.charAt(0).toUpperCase() + data.provider.slice(1);
                let modelName = data.model;
                let iconPath = '';
                
                if (data.provider === 'openai') {
                    iconPath = openaiIconPath;
                } else if (data.provider === 'perplexity') {
                    // Use the path from hidden field
                    iconPath = perplexityIconPath;
                }
                
                // Update badge and model info banner
                aiBadge.textContent = `${providerName} Powered`;
                aiBadge.setAttribute('data-provider', data.provider);
                
                // Update model info banner
                modelProviderIcon.src = iconPath;
                modelInfoText.innerHTML = `Powered by <strong>${providerName}</strong> — Model: <strong>${modelName}</strong>`;
            }
            
            // Re-enable input
            chatBotInput.disabled = false;
            chatBotSend.disabled = false;
            chatBotInput.focus();
        })
        .catch(error => {
            // Handle error
            chatBotMessages.removeChild(typingIndicator);
            console.error('Error:', error);
            
            // Add error message
            const errorMessage = document.createElement('div');
            errorMessage.classList.add('chat-bot-message', 'bot', 'error');
            errorMessage.innerHTML = `
                <div class="chat-bot-message-content">
                    <p>Sorry, I encountered an error processing your request. Please try again.</p>
                    <p><small>${error.message}</small></p>
                </div>
            `;
            chatBotMessages.appendChild(errorMessage);
            
            // Re-enable input
            chatBotInput.disabled = false;
            chatBotSend.disabled = false;
        });
    }
    
    // Clear error message when user starts typing
    chatBotInput.addEventListener('input', () => {
        const errorMessage = document.querySelector('.chat-bot-message.error');
        if (errorMessage) {
            chatBotMessages.removeChild(errorMessage);
        }
    });
}); 