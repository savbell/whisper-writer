// DOM Elements
const recordButton = document.getElementById('recordButton');
const statusText = document.getElementById('status');
const languageSelect = document.getElementById('language');
const apiKeyInput = document.getElementById('apiKey');
const saveButton = document.getElementById('saveSettings');

// State
let isRecording = false;

// Load saved settings
chrome.storage.local.get(['apiKey', 'language'], (result) => {
  if (result.apiKey) {
    apiKeyInput.value = result.apiKey;
    statusText.textContent = 'Ready';
    statusText.className = 'status';
  } else {
    statusText.textContent = 'Enter API key in settings';
    statusText.className = 'status error';
  }
  if (result.language) languageSelect.value = result.language;
});

// Save settings
saveButton.addEventListener('click', () => {
  const settings = {
    apiKey: apiKeyInput.value,
    language: languageSelect.value
  };
  
  chrome.storage.local.set(settings, () => {
    statusText.textContent = 'Settings saved!';
    statusText.className = 'status success';
    setTimeout(() => {
      if (settings.apiKey) {
        statusText.textContent = 'Ready';
        statusText.className = 'status';
      } else {
        statusText.textContent = 'Enter API key in settings';
        statusText.className = 'status error';
      }
    }, 2000);
  });
});

// Handle recording
recordButton.addEventListener('click', async () => {
  if (!isRecording) {
    // Check API key
    if (!apiKeyInput.value) {
      statusText.textContent = 'Please enter your API key in settings';
      statusText.className = 'status error';
      setTimeout(() => {
        statusText.textContent = 'Enter API key in settings';
        statusText.className = 'status error';
      }, 3000);
      return;
    }

    // Start recording
    isRecording = true;
    recordButton.textContent = 'Stop';
    recordButton.classList.add('recording');
    statusText.textContent = 'Recording...';
    statusText.className = 'status loading';
    
    // Send message to background script to start recording
    chrome.runtime.sendMessage({ 
      action: 'startRecording',
      language: languageSelect.value
    }, (response) => {
      if (!response || !response.success) {
        const error = response?.error || 'Failed to start recording';
        console.error('Recording error:', error);
        statusText.textContent = error;
        statusText.className = 'status error';
        isRecording = false;
        recordButton.textContent = 'Record';
        recordButton.classList.remove('recording');
        
        // Show microphone permission instructions if needed
        if (error.includes('denied') || error.includes('access')) {
          setTimeout(() => {
            statusText.textContent = 'Click the microphone icon in the address bar';
            statusText.className = 'status error';
          }, 3000);
        } else {
          setTimeout(() => {
            statusText.textContent = 'Ready';
            statusText.className = 'status';
          }, 3000);
        }
      }
    });
  } else {
    // Stop recording
    isRecording = false;
    recordButton.textContent = 'Record';
    recordButton.classList.remove('recording');
    statusText.textContent = 'Processing...';
    statusText.className = 'status loading';
    
    // Send message to background script to stop recording
    chrome.runtime.sendMessage({ action: 'stopRecording' }, (response) => {
      if (response.success) {
        statusText.textContent = 'Done!';
        statusText.className = 'status success';
        setTimeout(() => {
          statusText.textContent = 'Ready';
          statusText.className = 'status';
        }, 2000);
      } else {
        statusText.textContent = response.error || 'Error occurred';
        statusText.className = 'status error';
        setTimeout(() => {
          statusText.textContent = 'Ready';
          statusText.className = 'status';
        }, 3000);
      }
    });
  }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === 'recordingError') {
    console.error('Recording error:', message.error);
    isRecording = false;
    recordButton.textContent = 'Record';
    recordButton.classList.remove('recording');
    statusText.textContent = message.error;
    statusText.className = 'status error';
    
    // Show microphone permission instructions if needed
    if (message.error.includes('denied') || message.error.includes('access')) {
      setTimeout(() => {
        statusText.textContent = 'Click the microphone icon in the address bar';
        statusText.className = 'status error';
      }, 3000);
    } else {
      setTimeout(() => {
        statusText.textContent = 'Ready';
        statusText.className = 'status';
      }, 3000);
    }
  }
});