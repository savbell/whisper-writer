// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'insertText') {
    insertText(message.text);
    sendResponse({ success: true });
  }
});

// Insert text into active element
function insertText(text) {
  const activeElement = document.activeElement;
  
  // Check if element is editable
  if (isEditableElement(activeElement)) {
    // Handle different types of editable elements
    if (activeElement.isContentEditable) {
      // For contentEditable elements (like Google Docs)
      insertIntoContentEditable(activeElement, text);
    } else {
      // For regular input fields and textareas
      insertIntoInputField(activeElement, text);
    }
  }
}

// Check if element is editable
function isEditableElement(element) {
  return element && (
    element.isContentEditable ||
    element.tagName === 'INPUT' ||
    element.tagName === 'TEXTAREA'
  );
}

// Insert text into regular input fields
function insertIntoInputField(element, text) {
  const start = element.selectionStart;
  const end = element.selectionEnd;
  const before = element.value.substring(0, start);
  const after = element.value.substring(end);
  
  // Update value and cursor position
  element.value = before + text + after;
  const newCursor = start + text.length;
  element.setSelectionRange(newCursor, newCursor);
  
  // Trigger input event for reactive frameworks
  element.dispatchEvent(new Event('input', { bubbles: true }));
}

// Insert text into contentEditable elements
function insertIntoContentEditable(element, text) {
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  
  // Create text node
  const textNode = document.createTextNode(text);
  
  // Delete selected text if any
  range.deleteContents();
  
  // Insert new text
  range.insertNode(textNode);
  
  // Move cursor to end of inserted text
  range.setStartAfter(textNode);
  range.setEndAfter(textNode);
  selection.removeAllRanges();
  selection.addRange(range);
  
  // Trigger input event
  element.dispatchEvent(new Event('input', { bubbles: true }));
}

// Request microphone access
async function requestMicrophoneAccess() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: true,
      video: false
    });
    // Stop the stream immediately, we just wanted the permission
    stream.getTracks().forEach(track => track.stop());
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: 'Microphone access denied. Please allow access in your browser settings.' 
    };
  }
}