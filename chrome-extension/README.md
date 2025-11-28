# Luminate AITutor Chrome Extension

A Chrome extension that provides AI-powered tutoring assistance directly within the Centennial College Luminate platform.

## Features

- 🤖 Floating chatbot panel on Luminate pages
- 💬 Clean, modern chat interface
- 🎨 Beautiful gradient design with smooth animations
- 📱 Responsive design that works on different screen sizes
- ⚡ Fast and lightweight

## Installation

### Loading as an Unpacked Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension should now be loaded and active

### Verify Installation

1. Navigate to `https://luminate.centennialcollege.ca/ultra/institution-page` (or any Luminate page)
2. You should see the AITutor chatbot panel in the bottom-right corner
3. Try sending a message to test the interface

## Project Structure

```
chrome-extension/
├── manifest.json          # Extension configuration (Manifest V3)
├── contentScript.js       # Main logic for chatbot injection and handling
├── styles.css            # All styling for the chatbot UI
└── README.md             # This file
```

## Current Functionality

### Working Features
- ✅ Chatbot panel injection on Luminate pages
- ✅ Message input and display
- ✅ User/AI message differentiation
- ✅ Auto-scrolling chat area
- ✅ Enter key to send messages
- ✅ Welcome message on load

### Placeholder Features (To Be Implemented)
- ⏳ Real AI API integration (currently uses placeholder responses)
- ⏳ Conversation persistence
- ⏳ Loading indicators
- ⏳ Error handling UI

## Connecting to Real AI Backend

The extension is designed to connect to your AITutor backend. To integrate:

1. Open `contentScript.js`
2. Find the `getAiResponse()` function (around line 110)
3. Replace the placeholder code with your actual API call:

```javascript
async function getAiResponse(userMessage) {
  try {
    const response = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: userMessage,
        conversation_id: getCurrentConversationId(), // Implement this
        turn_index: getCurrentTurnIndex() // Implement this
      })
    });
    
    const data = await response.json();
    return data.answer || 'Sorry, I couldn\'t process that request.';
  } catch (error) {
    console.error('AI API Error:', error);
    return 'Sorry, I\'m having trouble connecting right now.';
  }
}
```

4. You'll need to handle CORS if your backend is on a different domain
5. Add the backend URL to `permissions` in `manifest.json` if needed

## Customization

### Changing the URL Pattern

Edit `manifest.json` to match your Luminate URL:

```json
"matches": [
  "https://your-actual-luminate-url.com/*"
]
```

### Styling

All styles are in `styles.css`. Key customization points:

- **Colors**: Modify the gradient colors in `.aitutor-header` and button styles
- **Size**: Change `width` and `height` in `.aitutor-panel`
- **Position**: Modify `bottom` and `right` properties in `.aitutor-panel`

### Adding Icons

The manifest references icons that aren't included. To add custom icons:

1. Create PNG images at 16x16, 48x48, and 128x128 pixels
2. Name them `icon16.png`, `icon48.png`, `icon128.png`
3. Place them in the `chrome-extension` folder

Or remove the `icons` section from `manifest.json` if you don't need custom icons.

## Troubleshooting

### Extension Not Loading
- Check that Developer mode is enabled
- Verify all files are in the correct directory
- Check the Chrome console for errors

### Chatbot Not Appearing
- Verify you're on the correct Luminate URL
- Check browser console for errors (F12 → Console)
- Make sure the URL pattern in `manifest.json` matches your Luminate URL

### Messages Not Sending
- Open browser console and check for JavaScript errors
- Verify the input field has focus
- Try reloading the page

## Development

### Testing Changes

1. Make changes to the code
2. Go to `chrome://extensions/`
3. Click the refresh icon on the Luminate AITutor extension
4. Reload the Luminate page to see changes

### Debugging

- Open Chrome DevTools (F12)
- Check the Console tab for errors
- Use `console.log()` statements in `contentScript.js`
- Inspect the chatbot panel using the Elements tab

## Future Enhancements

Potential features to add:

- [ ] Minimize/maximize button for the chatbot
- [ ] Conversation history persistence (localStorage or backend)
- [ ] Typing indicators when AI is "thinking"
- [ ] Rich text formatting (markdown, code blocks)
- [ ] File/image attachment support
- [ ] Dark mode toggle
- [ ] Settings panel
- [ ] Keyboard shortcuts
- [ ] Voice input
- [ ] Multi-language support

## License

This extension is part of the AiTutor project.

## Support

For issues or questions, please contact your development team or refer to the main AiTutor project documentation.
