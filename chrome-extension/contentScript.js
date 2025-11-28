/**
 * AITutor Chrome Extension - Content Script
 * 
 * This script injects a floating chatbot panel into the Luminate page.
 * The chatbot appears in the bottom-right corner and provides AI tutoring assistance.
 */

(function() {
  'use strict';

  // Prevent multiple injections if the script runs more than once
  if (document.getElementById('aitutor-container')) {
    return;
  }

  // ============================================================
  // DOM CREATION - Build the chatbot UI
  // ============================================================

  /**
   * Creates the main chatbot container and all UI elements
   */
  function createChatbotUI() {
    // Main container
    const container = document.createElement('div');
    container.id = 'aitutor-container';
    container.className = 'aitutor-panel';

    // Header
    const header = document.createElement('div');
    header.className = 'aitutor-header';
    
    const title = document.createElement('span');
    title.textContent = 'AITutor';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'aitutor-close-button';
    closeButton.innerHTML = '×';
    closeButton.title = 'Close chatbot';
    
    header.appendChild(title);
    header.appendChild(closeButton);

    // Messages area (scrollable)
    const messagesArea = document.createElement('div');
    messagesArea.id = 'aitutor-messages';
    messagesArea.className = 'aitutor-messages';

    // Input area container
    const inputArea = document.createElement('div');
    inputArea.className = 'aitutor-input-area';

    // Text input field
    const input = document.createElement('input');
    input.type = 'text';
    input.id = 'aitutor-input';
    input.className = 'aitutor-input';
    input.placeholder = 'Type your question...';

    // Send button
    const sendButton = document.createElement('button');
    sendButton.id = 'aitutor-send';
    sendButton.className = 'aitutor-send-button';
    sendButton.textContent = 'Send';

    // Assemble the DOM structure
    inputArea.appendChild(input);
    inputArea.appendChild(sendButton);

    container.appendChild(header);
    container.appendChild(messagesArea);
    container.appendChild(inputArea);

    // Create floating toggle button (to reopen chatbot)
    const toggleButton = document.createElement('button');
    toggleButton.id = 'aitutor-toggle';
    toggleButton.className = 'aitutor-toggle-button';
    toggleButton.innerHTML = '💬';
    toggleButton.title = 'Open AITutor';
    toggleButton.style.display = 'none'; // Hidden initially

    // Inject into the page
    document.body.appendChild(container);
    document.body.appendChild(toggleButton);

    return { container, messagesArea, input, sendButton, toggleButton };
  }

  // ============================================================
  // MESSAGE HANDLING
  // ============================================================

  /**
   * Adds a message to the chat window
   * @param {string} text - The message content
   * @param {string} sender - Either 'user' or 'ai'
   */
  function addMessage(text, sender = 'user') {
    const messagesArea = document.getElementById('aitutor-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `aitutor-message aitutor-message-${sender}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'aitutor-message-content';
    
    // Format text with proper line breaks and basic markdown
    let formattedText = text
      // Convert double newlines to paragraph breaks
      .replace(/\n\n/g, '<br><br>')
      // Convert single newlines to line breaks
      .replace(/\n/g, '<br>')
      // Convert **bold** to <strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Convert bullet points with proper spacing
      .replace(/- /g, '• ');
    
    messageContent.innerHTML = formattedText;
    
    messageDiv.appendChild(messageContent);
    messagesArea.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }

  /**
   * Displays the initial welcome message from AITutor
   */
  function showWelcomeMessage() {
    addMessage('Hi! I\'m AITutor. How can I help you with Luminate today?', 'ai');
  }

  // ============================================================
  // CONVERSATION STATE MANAGEMENT
  // ============================================================

  let conversationId = null;
  let turnIndex = 0;

  /**
   * Gets or creates a conversation ID for this session
   */
  function getConversationId() {
    if (!conversationId) {
      // Generate a unique conversation ID
      conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    return conversationId;
  }

  /**
   * Gets and increments the turn index
   */
  function getAndIncrementTurnIndex() {
    const current = turnIndex;
    turnIndex++;
    return current;
  }

  // ============================================================
  // AI RESPONSE (REAL API INTEGRATION)
  // ============================================================

  /**
   * Gets a response from the AI tutoring backend
   * 
   * Connects to the FastAPI backend running on localhost:8000
   * Sends user question and receives AI tutor response
   * 
   * @param {string} userMessage - The user's question/input
   * @returns {Promise<string>} - The AI's response
   */
  async function getAiResponse(userMessage) {
    try {
      console.log('[AITutor] Sending message to backend:', userMessage);
      
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          conversation_id: getConversationId(),
          turn_index: getAndIncrementTurnIndex()
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('[AITutor] Received response from backend:', data);
      
      // Extract the main answer from the response
      // The backend returns { conversation_id, output, plan, outputs, ... }
      const answer = data.output || data.answer || 'Sorry, I couldn\'t process that request.';
      
      return answer;
      
    } catch (error) {
      console.error('[AITutor] API Error:', error);
      
      // Check if it's a network error (backend not running)
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return 'Sorry, I can\'t connect to the AI backend. Please make sure the server is running at http://localhost:8000';
      }
      
      return `Sorry, something went wrong: ${error.message}`;
    }
  }

  // ============================================================
  // USER INTERACTION HANDLING
  // ============================================================

  /**
   * Handles sending a message when user clicks Send or presses Enter
   */
  async function handleSendMessage() {
    const input = document.getElementById('aitutor-input');
    const sendButton = document.getElementById('aitutor-send');
    const message = input.value.trim();

    // Don't send empty messages
    if (!message) {
      return;
    }

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input field
    input.value = '';

    // Disable input while processing
    input.disabled = true;
    sendButton.disabled = true;
    sendButton.textContent = 'Thinking...';

    // Show loading message
    const loadingId = 'loading_' + Date.now();
    const messagesArea = document.getElementById('aitutor-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'aitutor-message aitutor-message-ai';
    loadingDiv.innerHTML = '<div class="aitutor-message-content aitutor-loading">● ● ●</div>';
    messagesArea.appendChild(loadingDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;

    // Get AI response
    try {
      const aiResponse = await getAiResponse(message);
      
      // Remove loading message
      const loadingElement = document.getElementById(loadingId);
      if (loadingElement) {
        loadingElement.remove();
      }
      
      // Add AI response
      addMessage(aiResponse, 'ai');
    } catch (error) {
      console.error('Error getting AI response:', error);
      
      // Remove loading message
      const loadingElement = document.getElementById(loadingId);
      if (loadingElement) {
        loadingElement.remove();
      }
      
      addMessage('Sorry, something went wrong. Please try again.', 'ai');
    } finally {
      // Re-enable input
      input.disabled = false;
      sendButton.disabled = false;
      sendButton.textContent = 'Send';
      input.focus();
    }
  }

  /**
   * Sets up all event listeners for the chatbot
   */
  function setupEventListeners(input, sendButton) {
    // Send button click
    sendButton.addEventListener('click', handleSendMessage);

    // Enter key press in input field
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleSendMessage();
      }
    });
    
    // Close button click
    const closeButton = document.querySelector('.aitutor-close-button');
    const toggleButton = document.getElementById('aitutor-toggle');
    if (closeButton) {
      closeButton.addEventListener('click', () => {
        const container = document.getElementById('aitutor-container');
        if (container) {
          container.style.display = 'none';
          if (toggleButton) {
            toggleButton.style.display = 'flex';
          }
        }
      });
    }
    
    // Toggle button click (reopen chatbot)
    if (toggleButton) {
      toggleButton.addEventListener('click', () => {
        const container = document.getElementById('aitutor-container');
        if (container) {
          container.style.display = 'flex';
          toggleButton.style.display = 'none';
        }
      });
    }
  }

  // ============================================================
  // INITIALIZATION
  // ============================================================

  /**
   * Main initialization function
   * Creates the UI and sets up the chatbot
   */
  function init() {
    console.log('AITutor Chrome Extension loaded');

    // Create the chatbot UI
    const { messagesArea, input, sendButton } = createChatbotUI();

    // Show welcome message
    showWelcomeMessage();

    // Set up event listeners
    setupEventListeners(input, sendButton);
  }

  // Wait for DOM to be fully loaded (though we use document_end, this is a safety check)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
