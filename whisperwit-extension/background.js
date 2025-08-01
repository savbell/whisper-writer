// Audio recording state
let mediaRecorder = null;
let audioChunks = [];

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startRecording') {
    // Start recording directly in the background script
    startRecording(message.language)
      .then(() => sendResponse({ success: true }))
      .catch(error => {
        console.error('Recording error:', error);
        sendResponse({ success: false, error: error.message });
        chrome.runtime.sendMessage({ 
          action: 'recordingError', 
          error: error.message 
        });
      });
    return true; // Keep message channel open for async response
  }
  
  if (message.action === 'stopRecording') {
    stopRecording()
      .then(text => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          chrome.tabs.sendMessage(tabs[0].id, {
            action: 'insertText',
            text: text
          });
        });
        sendResponse({ success: true, text: text });
      })
      .catch(error => {
        console.error('Stop recording error:', error);
        sendResponse({ success: false, error: error.message });
        chrome.runtime.sendMessage({
          action: 'recordingError',
          error: error.message
        });
      });
    return true; // Keep message channel open for async response
  }
});

// Start recording
async function startRecording(language) {
  if (mediaRecorder) {
    throw new Error('Recording already in progress');
  }

  try {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      }
    });

    // Create MediaRecorder
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm'
    });
    audioChunks = [];

    // Set up data handling
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    // Handle errors
    mediaRecorder.onerror = (event) => {
      console.error('MediaRecorder error:', event.error);
      throw new Error('Recording failed: ' + event.error.message);
    };

    // Start recording
    mediaRecorder.start(1000); // Collect data every second
  } catch (error) {
    console.error('Start recording error:', error);
    if (error.name === 'NotAllowedError') {
      throw new Error('Microphone access denied. Please allow access in your browser settings.');
    } else if (error.name === 'NotFoundError') {
      throw new Error('No microphone found. Please check your microphone connection.');
    } else if (error.name === 'NotReadableError') {
      throw new Error('Could not access microphone. It may be in use by another application.');
    } else {
      throw new Error('Could not start recording: ' + error.message);
    }
  }
}

// Stop recording and transcribe
async function stopRecording() {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) {
      reject(new Error('No recording in progress'));
      return;
    }

    mediaRecorder.onstop = async () => {
      try {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const transcript = await transcribeAudio(audioBlob);
        const enhancedTranscript = await enhanceTranscription(transcript);
        resolve(enhancedTranscript);
      } catch (error) {
        console.error('Transcription error:', error);
        reject(error);
      } finally {
        // Clean up
        if (mediaRecorder && mediaRecorder.stream) {
          mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        mediaRecorder = null;
        audioChunks = [];
      }
    };

    mediaRecorder.stop();
  });
}

// Transcribe audio using Whisper API
async function transcribeAudio(audioBlob) {
  // Get API key from storage
  const { apiKey } = await chrome.storage.local.get(['apiKey']);
  if (!apiKey) {
    throw new Error('Please set your OpenAI API key in settings');
  }

  // Create form data
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');
  formData.append('model', 'whisper-1');

  try {
    const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('API error:', error);
      throw new Error(error.error?.message || 'Transcription failed');
    }

    const result = await response.json();
    return result.text;
  } catch (error) {
    console.error('Transcription API error:', error);
    throw new Error('Transcription failed: ' + error.message);
  }
}

async function enhanceTranscription(transcript) {
  const { apiKey } = await chrome.storage.local.get(['apiKey']);
  if (!apiKey) {
    throw new Error('Please set your OpenAI API key in settings');
  }
  const body = {
    model: "gpt-4o",
    messages: [
      { role: "system", content: "You are a transcription enhancement assistant. Refine the text for clarity, punctuation, and grammar." },
      { role: "user", content: transcript }
    ],
    temperature: 0.0
  };
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    });
    if (!response.ok) {
      const error = await response.json();
      console.error('ChatGPT API error:', error);
      throw new Error(error.error?.message || 'ChatGPT enhancement failed');
    }
    const result = await response.json();
    return result.choices[0].message.content.trim();
  } catch (error) {
    console.error('Enhancement error:', error);
    throw new Error('ChatGPT enhancement failed: ' + error.message);
  }
}