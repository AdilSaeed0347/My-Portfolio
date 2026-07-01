class PortfolioChatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.localStorageKey = "portfolioChatHistory";
        this.backendUrl = (window.CONFIG && window.CONFIG.BACKEND_URL
           ? window.CONFIG.BACKEND_URL
           : "http://127.0.0.1:8000") + "/api/v1/chat";
        this.isTyping = false;
        this.isUserScrolling = false;
        this.isGeneratingResponse = false;
        this.lastScrollTime = 0;
        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        this.securityKeywords = ['murder', 'weapon', 'bomb', 'terrorism', 'hate', 'fuck', 'sex'];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadHistory();
        this.setupMicrophone();
        this.injectSimpleStyles();
        
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) chatMessages.addEventListener('scroll', () => this.handleScroll());
        this.showWelcomePopup();
    }

    bindEvents() {
        const chatButton = document.getElementById('chatbot-button');
        const closeBtn = document.querySelector('.close-chat');
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');

        if (chatButton) chatButton.addEventListener('click', () => this.openChat());
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeChat());
        if (sendBtn) sendBtn.addEventListener('click', () => {
            if (!this.isTyping && chatInput?.value.trim()) this.sendMessage();
        });
        
        if (chatInput) {
            chatInput.addEventListener('input', () => this.updateButtonState());
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey && !this.isTyping && chatInput.value.trim()) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    showWelcomePopup() {
        const welcomePopup = document.getElementById("chatbot-welcome");
        const chatButton = document.getElementById("chatbot-button");

        if (!welcomePopup) return;

        setTimeout(() => {
            welcomePopup.classList.remove("hidden");
            setTimeout(() => {
                welcomePopup.classList.add("hidden");
            }, 6000);
        }, 2000);

        if (chatButton) {
            chatButton.addEventListener("click", () => {
                welcomePopup.classList.add("hidden");
            });
        }
    }

    setupMicrophone() {
        const micBtn = document.getElementById('micBtn');
        if (!micBtn || !('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            if (micBtn) micBtn.style.display = 'none';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = () => micBtn.classList.add('listening');
        recognition.onend = () => micBtn.classList.remove('listening');
        recognition.onresult = (event) => {
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.value = event.results[0][0].transcript;
                this.updateButtonState();
                if (!this.isGeneratingResponse) chatInput.focus();
            }
        };
        
        micBtn.addEventListener('click', () => recognition.start());
    }

    updateButtonState() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const micBtn = document.getElementById('micBtn');
        if (!chatInput || !sendBtn) return;
        
        const hasText = chatInput.value.trim() !== "";
        if (hasText) {
            sendBtn.innerHTML = "➤";
            sendBtn.style.display = "inline-flex";
            if (micBtn) micBtn.style.display = "none";
        } else {
            sendBtn.style.display = "none";
            if (micBtn) micBtn.style.display = "inline-flex";
        }
    }

    handleScroll() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        const threshold = 30;
        const distanceFromBottom = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight;
        this.isUserScrolling = distanceFromBottom > threshold;
    }

    validateInput(input) {
        const inputLower = input.toLowerCase();
        
        let cleanedInput = inputLower;
        if (inputLower.includes('skill') || inputLower.includes('skil')) {
            cleanedInput = inputLower.replace(/skills?|skils?/g, '');
        }
        
        const foundKeywords = this.securityKeywords.filter(keyword => {
            if (keyword === 'kill') {
                return cleanedInput.includes('kill');
            }
            return inputLower.includes(keyword);
        });
        
        if (foundKeywords.length > 0) {
            return { isValid: false, message: 'I can only assist with professional questions about Adil\'s portfolio and work.' };
        }
        
        if (input.length > 500) {
            return { isValid: false, message: 'Please keep your question under 500 characters.' };
        }
        
        return { isValid: true };
    }

    loadHistory() {
        try {
            const sessionHistory = localStorage.getItem(this.localStorageKey);
            if (sessionHistory) {
                const parsed = JSON.parse(sessionHistory);
                if (Array.isArray(parsed)) {
                    this.messages = parsed.slice(-50);
                    const chatMessages = document.getElementById('chat-messages');
                    if (chatMessages) chatMessages.innerHTML = '';
                    this.messages.forEach(msg => this.renderMessage(msg));
                    this.scrollToBottom(true);
                    return;
                }
            }
        } catch (error) {
            console.warn('Error loading chat history:', error);
            localStorage.removeItem(this.localStorageKey);
        }
        this.loadInitialMessage();
    }

    loadInitialMessage() {
        const welcomeMessage = {
            id: this.generateMessageId(),
            text: "Hi! I'm Adil Saeed's AI Assistant. Ask me about his projects, skills, education, or contact information.\n\nI'm Adil Saeed's AI Assistant.",
            isUser: false,
            timestamp: new Date().toISOString(),
            type: 'welcome',
            isDefaultMessage: true
        };
        this.messages.push(welcomeMessage);
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) chatMessages.innerHTML = '';
        this.renderMessage(welcomeMessage);
        this.saveHistory();
        this.scrollToBottom(true);
    }

    openChat() {
        const chatWindow = document.getElementById('chat-window');
        const chatButton = document.getElementById('chatbot-button');
        const welcomePopup = document.getElementById("chatbot-welcome");

        if (chatWindow && chatButton) {
            this.isOpen = true;
            chatButton.style.display = 'none';
            chatWindow.classList.remove('hidden');
            if (welcomePopup) welcomePopup.classList.add("hidden");
            this.scrollToBottom(true);
            this.updateButtonState();
            setTimeout(() => document.getElementById('chat-input')?.focus(), 100);
        }
    }

    closeChat() {
        const chatWindow = document.getElementById('chat-window');
        const chatButton = document.getElementById('chatbot-button');
        if (chatWindow && chatButton) {
            this.isOpen = false;
            chatWindow.classList.add('hidden');
            chatButton.style.display = 'flex';
            this.hideTypingIndicator();
        }
    }

    async sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const messageText = chatInput?.value.trim();

        if (!messageText || this.isTyping || this.isGeneratingResponse) return;

        const validation = this.validateInput(messageText);
        if (!validation.isValid) {
            this.showValidationError(validation.message);
            return;
        }

        this.isTyping = true;
        this.isGeneratingResponse = true;
        this.addMessage(messageText, true);
        this.scrollToBottom(true);

        chatInput.value = '';
        this.updateButtonState();
        chatInput.disabled = true;
        if (sendBtn) sendBtn.disabled = true;

        try {
            this.showTypingIndicator();
            const botResponse = await this.getBotResponse(messageText);
            this.hideTypingIndicator();
            
            await this.streamMessageText(botResponse.answer || botResponse, {
                sources: botResponse.sources || [],
                queryType: botResponse.query_type || 'unknown',
                images: botResponse.images || [],
                showImagesAfter: botResponse.show_images_after_ms || 0
            });
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Chat error:', error);
            await this.streamMessageText(this.getErrorMessage(error), { type: 'error' });
        } finally {
            this.isTyping = false;
            this.isGeneratingResponse = false;
            chatInput.disabled = false;
            if (sendBtn) sendBtn.disabled = false;
            this.updateButtonState();
            chatInput.focus();
        }
    }

    async streamMessageText(text, metadata = {}) {
        const messageId = this.generateMessageId();
        const message = {
            id: messageId,
            text: text,
            isUser: false,
            timestamp: new Date().toISOString(),
            metadata: metadata,
            isDefaultMessage: false
        };
        this.messages.push(message);
        this.saveHistory();

        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.id = messageId;

        messageElement.innerHTML = `
            <div class="message-content"></div>
            <div class="message-actions">
                <button class="action-btn copy-btn" data-message-id="${messageId}" title="Copy message">
                    ⧉
                </button>
                <button class="action-btn regenerate-btn" data-message-id="${messageId}" title="Regenerate response">
                    🔄
                </button>
            </div>
            <div class="message-time">${this.formatTime(new Date(message.timestamp))}</div>
        `;
        chatMessages.appendChild(messageElement);

        const contentDiv = messageElement.querySelector('.message-content');

        // Parse and prepare the text with signature at the end
        let mainText = text;
        let hasSignature = false;
        
        // Check if text contains the signature
        if (text.includes('📚 Adil Data')) {
            mainText = text.replace(/📚 Adil Data/g, '').trim();
            hasSignature = true;
        }

        const fullFormattedText = this.parseSimpleMarkdown(mainText);

        // Stream the main content smoothly
        let i = 0;
        let currentHTML = '';

        while (i < fullFormattedText.length) {
            if (!this.isGeneratingResponse) break;

            if (fullFormattedText[i] === '<') {
                const tagEnd = fullFormattedText.indexOf('>', i);
                if (tagEnd !== -1) {
                    currentHTML = fullFormattedText.slice(0, tagEnd + 1);
                    contentDiv.innerHTML = currentHTML;
                    i = tagEnd + 1;

                    if (Date.now() - this.lastScrollTime >= 50) {
                        this.scrollToBottom();
                        this.lastScrollTime = Date.now();
                    }
                    await this.sleep(1);
                    continue;
                }
            }

            currentHTML = fullFormattedText.slice(0, i + 1);
            contentDiv.innerHTML = currentHTML;

            if (Date.now() - this.lastScrollTime >= 100) {
                this.scrollToBottom();
                this.lastScrollTime = Date.now();
            }

            await this.sleep(3);
            i++;
        }

        // Add signature cleanly at the end if it exists
        if (hasSignature) {
            const signatureHTML = '<div class="message-signature">📚 Adil Data</div>';
            contentDiv.innerHTML = currentHTML + signatureHTML;
        }
        
        // Attach event listeners after streaming completes
        const copyBtn = messageElement.querySelector('.copy-btn');
        const regenBtn = messageElement.querySelector('.regenerate-btn');

        if (copyBtn) {
            copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.copyMessage(messageId);
            });
        }

        if (regenBtn) {
            regenBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.regenerateResponse(messageId);
            });
        }
        
        // Handle images with streaming effect
        if (metadata.images && metadata.images.length > 0) {
            await this.handleImageDisplay(messageElement, metadata.images, metadata.showImagesAfter || 2500);
        }
        
        this.scrollToBottom();
    }

    async handleImageDisplay(messageElement, images, delay) {
        const messageContent = messageElement.querySelector('.message-content');
        
        const imageSpinner = document.createElement('div');
        imageSpinner.className = 'image-spinner';
        imageSpinner.innerHTML = `
            <div class="image-loading">
                <div class="loading-spinner"></div>
                <span>Generating image...</span>
            </div>
        `;
        messageContent.appendChild(imageSpinner);
        this.scrollToBottom();
        
        await this.sleep(delay);
        
        imageSpinner.remove();
        
        const imageGallery = document.createElement('div');
        imageGallery.className = 'image-gallery';
        
        for (const img of images) {
            const imageCard = document.createElement('div');
            imageCard.className = 'image-card';
            imageCard.style.opacity = '0';
            
            const imageEl = document.createElement('img');
            imageEl.src = `/rag/documents/images/${img.file || img}`;
            imageEl.alt = img.alt || 'Image from Adil\'s portfolio';
            imageEl.className = 'chat-image';
            
            const caption = document.createElement('div');
            caption.className = 'image-caption';
            caption.textContent = img.caption || 'Portfolio Image';
            
            imageCard.appendChild(imageEl);
            imageCard.appendChild(caption);
            imageGallery.appendChild(imageCard);
            
            setTimeout(() => {
                imageCard.style.transition = 'opacity 0.4s ease';
                imageCard.style.opacity = '1';
            }, 100);
        }
        
        messageContent.appendChild(imageGallery);
        this.scrollToBottom();
    }

    async getBotResponse(userMessage) {
        try {
            const response = await fetch(this.backendUrl, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Accept': 'application/json' 
                },
                body: JSON.stringify({
                    query: userMessage,
                    language: /[\u0600-\u06FF]/.test(userMessage) ? 'ur' : 'en',
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString(),
                    conversation_history: this.messages.slice(-10).map(msg => ({
                        role: msg.isUser ? 'user' : 'assistant',
                        content: msg.text,
                        timestamp: msg.timestamp || new Date().toISOString()
                    }))
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Backend connection error:', error);
            throw error;
        }
    }

    getErrorMessage(error) {
        if (error.message.includes('Failed to fetch')) return "Connection error. Check your internet connection.";
        return "I encountered an error. Please try again.";
    }

    addMessage(text, isUser, metadata = {}) {
        const message = {
            id: this.generateMessageId(),
            text: text,
            isUser: isUser,
            timestamp: new Date().toISOString(),
            metadata: metadata,
            isDefaultMessage: false
        };
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        this.saveHistory();
    }

    renderMessage(message) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.isUser ? 'user-message' : 'bot-message'}`;
        messageElement.id = message.id;
        
        if (message.metadata && message.metadata.regenerated) {
            messageElement.setAttribute('data-regenerated', 'true');
        }
        
        let displayText = message.text;
        let hasSignature = false;
        
        if (displayText.includes('📚 Adil Data')) {
            displayText = displayText.replace(/📚 Adil Data/g, '').trim();
            hasSignature = true;
        }
        
        const parsedText = message.isUser ? this.escapeHtml(displayText) : this.parseSimpleMarkdown(displayText);
        const timeString = this.formatTime(new Date(message.timestamp));
        
        if (message.isUser) {
            messageElement.innerHTML = `
                <div class="message-content">${parsedText}</div>
                <div class="message-time">${timeString}</div>
            `;
        } else {
            // Check if this is the default welcome message
            const isDefault = message.isDefaultMessage === true || message.type === 'welcome';
            
            let actionsHTML = '';
            if (!isDefault) {
                actionsHTML = `
                    <div class="message-actions">
                        <button class="action-btn copy-btn" data-message-id="${message.id}" title="Copy">⧉</button>
                        <button class="action-btn regenerate-btn" data-message-id="${message.id}" title="Regenerate">🔄</button>
                    </div>
                `;
            }
            
            let finalContent = parsedText;
            if (hasSignature) {
                finalContent += '<div class="message-signature">📚 Adil Data</div>';
            }
            
            messageElement.innerHTML = `
                <div class="message-content">${finalContent}</div>
                ${actionsHTML}
                <div class="message-time">${timeString}</div>
            `;
            
            if (!isDefault) {
                requestAnimationFrame(() => {
                    const copyBtn = messageElement.querySelector('.copy-btn');
                    const regenBtn = messageElement.querySelector('.regenerate-btn');
                    
                    if (copyBtn) copyBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.copyMessage(message.id);
                    });
                    
                    if (regenBtn) regenBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.regenerateResponse(message.id);
                    });
                });
            }
        }
        
        chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    parseSimpleMarkdown(text) {
        text = text.replace(/target="_blank"[^>]*>/g, '">');
        text = text.replace(/rel="[^"]*"/g, '');
        text = text.replace(/class="[^"]*">/g, '');

        text = this.escapeHtml(text);

        // Bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert markdown links to clickable links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" class="chat-link">$1</a>');

        // Line breaks
        text = text.replace(/\n\n/g, '<br><br>');
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    formatTime(date) {
        const hours = date.getHours();
        const minutes = date.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        const displayMinutes = minutes.toString().padStart(2, '0');
        return `${displayHours}:${displayMinutes} ${ampm}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    showValidationError(message) {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.style.borderColor = '#ff4444';
            setTimeout(() => chatInput.style.borderColor = '', 3000);
        }
        this.addMessage(`${message}`, false, { type: 'validation_error' });
    }

    saveHistory() {
        try {
            localStorage.setItem(this.localStorageKey, JSON.stringify(this.messages.slice(-50)));
        } catch (error) {
            console.warn('Error saving chat history:', error);
        }
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const existing = document.getElementById('typing-indicator');
        if (existing) existing.remove();
        
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot-message typing-indicator';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
            <div class="message-content">
                <div class="typing-animation">
                    <span></span><span></span><span></span>
                </div>
                <span class="typing-text"> Thinking...</span>
            </div>
        `;
        chatMessages.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) typingIndicator.remove();
    }

    scrollToBottom(force = false) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages || (this.isUserScrolling && !force)) return;
        requestAnimationFrame(() => chatMessages.scrollTop = chatMessages.scrollHeight);
    }

    injectSimpleStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            /* Smooth link rendering */
            .chat-link {
                color: #1a73e8 !important;
                text-decoration: none;
                font-weight: 500;
                cursor: pointer;
                transition: color 0.15s ease;
                display: inline;
            }
            .chat-link:hover {
                color: #1557b0 !important;
                text-decoration: underline;
            }
            .message-content strong {
                font-weight: 600;
            }
            
            /* Signature styling */
            .message-signature {
                margin-top: 12px;
                padding-top: 8px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 0.875rem;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            /* Image display styles */
            .image-gallery {
                display: flex;
                gap: 10px;
                margin-top: 12px;
                flex-wrap: wrap;
            }
            
            .image-card {
                max-width: 200px;
                border-radius: 12px;
                overflow: hidden;
                background: #f8f9fa;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: opacity 0.4s ease;
            }
            
            .chat-image {
                width: 100%;
                height: auto;
                display: block;
            }
            
            .image-caption {
                padding: 8px 12px;
                font-size: 13px;
                color: #666;
                border-top: 1px solid #eee;
            }
            
            /* Image loading spinner */
            .image-spinner {
                margin-top: 12px;
                padding: 12px;
                background: linear-gradient(90deg, #f0f2f6, #eef3ff);
                border-radius: 8px;
                display: inline-block;
            }
            
            .image-loading {
                display: flex;
                align-items: center;
                gap: 8px;
                font-style: italic;
                color: #666;
            }
            
            .loading-spinner {
                width: 16px;
                height: 16px;
                border: 2px solid #e3e3e3;
                border-top: 2px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Typing indicator animation */
            .typing-animation {
                display: inline-flex;
                gap: 3px;
                margin-right: 8px;
            }
            .typing-animation span {
                width: 6px;
                height: 6px;
                background: #3b82f6;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }
            .typing-animation span:nth-child(2) { animation-delay: 0.2s; }
            .typing-animation span:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typing {
                0%, 60%, 100% { 
                    transform: translateY(0); 
                    opacity: 0.4; 
                }
                30% { 
                    transform: translateY(-8px); 
                    opacity: 1; 
                }
            }
            
            .typing-text {
                color: #6b7280;
                font-style: italic;
            }
            
            /* Microphone listening state */
            #micBtn.listening {
                background-color: #fef3c7;
                border-color: #f59e0b;
            }
            
            /* Copy button feedback */
            .action-btn.copied {
                color: #10b981;
            }
        `;
        document.head.appendChild(styles);
    }

    copyMessage(messageId) {
        const message = this.messages.find(m => m.id === messageId);
        if (!message) {
            console.error('Message not found:', messageId);
            return;
        }
        
        const tempDiv = document.createElement('div');
        let textToCopy = message.text;
        
        // Remove signature from copy
        textToCopy = textToCopy.replace(/📚 Adil Data/g, '').trim();
        
        tempDiv.innerHTML = this.parseSimpleMarkdown(textToCopy);
        const plainText = tempDiv.textContent || tempDiv.innerText || '';
        
        navigator.clipboard.writeText(plainText).then(() => {
            const btn = document.querySelector(`.copy-btn[data-message-id="${messageId}"]`);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓';
                btn.classList.add('copied');
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            }
        }).catch(err => {
            console.error('Copy failed:', err);
            alert('Failed to copy message');
        });
    }

    async regenerateResponse(messageId) {
        const messageIndex = this.messages.findIndex(m => m.id === messageId);
        if (messageIndex === -1 || messageIndex === 0) {
            console.error('Cannot regenerate: message not found or is first message');
            return;
        }
        
        const userMessage = this.messages[messageIndex - 1];
        if (!userMessage || !userMessage.isUser) {
            console.error('Cannot find user message to regenerate from');
            return;
        }
        
        const regenBtn = document.querySelector(`.regenerate-btn[data-message-id="${messageId}"]`);
        if (regenBtn) {
            regenBtn.textContent = '⟳';
            regenBtn.classList.add('regenerating');
            regenBtn.disabled = true;
        }
        
        try {
            const reAskedMessage = {
                id: this.generateMessageId(),
                text: userMessage.text,
                isUser: true,
                timestamp: new Date().toISOString(),
                metadata: { regenerated: true }
            };
            
            this.messages.push(reAskedMessage);
            this.renderMessage(reAskedMessage);
            this.saveHistory();
            this.scrollToBottom(true);
            
            await this.sleep(300);
            
            this.isGeneratingResponse = true;
            this.showTypingIndicator();
            
            const botResponse = await this.getBotResponse(userMessage.text);
            this.hideTypingIndicator();
            
            await this.streamMessageText(botResponse.answer || botResponse, {
                sources: botResponse.sources || [],
                queryType: botResponse.query_type || 'unknown',
                images: botResponse.images || [],
                showImagesAfter: botResponse.show_images_after_ms || 0
            });
            
            this.scrollToBottom(true);
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Regeneration error:', error);
            await this.streamMessageText(this.getErrorMessage(error), { type: 'error' });
        } finally {
            this.isGeneratingResponse = false;
            
            if (regenBtn && regenBtn.parentElement) {
                regenBtn.textContent = '🔄';
                regenBtn.classList.remove('regenerating');
                regenBtn.disabled = false;
            }
        }
    }
}

// Initialize chatbot
document.addEventListener('DOMContentLoaded', function() {
    try {
        window.portfolioChatbot = new PortfolioChatbot();
        console.log('Enhanced chatbot initialized successfully');
    } catch (error) {
        console.error('Failed to initialize chatbot:', error);
    }
});