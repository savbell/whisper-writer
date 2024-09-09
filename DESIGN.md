
## 1. Core Components:

   a. AudioManager:
      - Manages its own thread, running for the duration of the program
      - Handles audio recording based on triggered shortcuts and recording modes
      - Supports both streaming and non-streaming modes
      - In streaming mode, continuously emits small audio chunks (e.g., 200ms) to a queue
      - In non-streaming mode, collects all audio before sending it to the queue
      - Uses sentinel values in the audio queue to signify the end of audio data
      - Uses session IDs to identify and manage individual recording sessions
      - Implements voice activity detection (VAD) for certain recording modes

   b. Profile:
      - Encapsulates related components and settings:
        - TranscriptionManager: Handles transcription for a specific backend, manages its own thread
        - PostProcessor: Applies post-processing to transcribed text
        - OutputManager: Handles output operations specific to the profile
        - StreamingResultHandler: Manages streaming results (for streaming mode only)
      - Associated with a specific activation shortcut
      - Maintains its state (IDLE, RECORDING, TRANSCRIBING)
      - Configurable for streaming or non-streaming transcription mode
      - Handles all result processing internally

   c. InputManager:
      - Runs on the main thread
      - Handles all input events (keyboard shortcuts, GUI interactions)
      - Maps shortcuts to specific profiles

   d. ConfigManager:
      - Manages global options and profile-specific configurations
      - Supports dynamic configuration updates
      - Implemented as a static class with class methods

   e. UIManager:
      - Manages all UI components:
        - MainWindow: Displayed only at program launch for initial setup
        - SettingsWindow: Accessible via tray icon menu for configuration
        - StatusWindow: Optional window that appears during recording and transcription
        - TrayIconManager: Manages the system tray icon and its menu
      - Handles UI-related logic and user interactions
      - Encapsulates all Qt-specific code except for EventBus

## 2. Main Application Flow:

   a. ApplicationController:
      - Runs on the main thread
      - Central coordinator for all core components
      - Manages the lifecycle of the application and profiles
      - Handles high-level logic for different operation modes (streaming and non-streaming)
      - Manages session IDs for each recording/transcription job
      - Activates/deactivates recording based on shortcuts and session IDs
      - Handles transcription completion and audio discarding events

## 3. Communication and Event Handling:

   a. EventBus:
      - Central event system for inter-component communication
      - Uses Qt signals to ensure events are processed on the main thread
      - Provides subscribe/unsubscribe functionality for event handling

   b. Queue:
      - Python's built-in Queue class is used, which is thread-safe by design
      - A separate queue is created for each profile to manage audio data
      - Used for passing audio data between AudioManager and TranscriptionManager within a profile

## 4. Threading Model:

   a. Main Thread:
      - Runs ApplicationController, InputManager, UIManager
      - Manages configuration changes and event routing
      - Processes all events emitted through EventBus

   b. Audio Thread:
      - Managed internally by AudioManager
      - Runs for the duration of the program
      - In streaming mode, continuously sends audio chunks to the queue
      - In non-streaming mode, sends complete audio data to the queue after recording finishes

   c. Transcription Threads:
      - Each TranscriptionManager manages its own thread
      - Run for the duration of their respective profiles
      - In streaming mode, continuously process incoming audio chunks
      - In non-streaming mode, process complete audio data after recording finishes

## 5. Session Management:

   - Each recording/transcription job is assigned a unique session ID (UUID)
   - Session IDs are used to track the lifecycle of each job from recording through transcription
   - ApplicationController maintains a mapping between session IDs and profiles
   - AudioManager and TranscriptionManager use session IDs to manage concurrent jobs

## 6. Workflow:

   1. Program launches, creates QApplication instance
   2. main() initializes UIManager, EventBus, ConfigManager, and ApplicationController
   3. UIManager displays MainWindow for initial setup
   4. After setup, MainWindow closes and TrayIconManager creates system tray icon
   5. ApplicationController initializes AudioManager, InputManager, and profiles based on configuration
   6. Profile(s) initializes its TranscriptionManager, OutputManager, and StreamingResultHandler (if in streaming mode)
   7. Audio and Transcription threads are started and run continuously
   8. InputManager listens for configured shortcuts
   9. When a shortcut is triggered, InputManager notifies ApplicationController via EventBus
   10. ApplicationController identifies the corresponding profile
   11. ApplicationController generates a new session ID and starts recording via AudioManager
   12. UIManager shows/updates StatusWindow if enabled
   13. AudioManager sends audio data to the profile's queue, either in chunks (streaming) or complete (non-streaming)
   14. TranscriptionManager processes audio from the profile's queue, using sentinel values to detect the end of audio data
   15. TranscriptionManager sends raw results to the Profile
   16. Profile processes the results:
       - Applies post-processing
       - For streaming mode: uses StreamingResultHandler to manage partial results and output
       - For non-streaming mode: outputs the complete result
   17. Profile manages its own state transitions and output
   18. Profile notifies ApplicationController when transcription is complete
   19. ApplicationController handles session cleanup and manages continuous recording if configured
   20. UIManager updates with partial results in streaming mode, or final results in non-streaming mode
   21. UIManager hides StatusWindow when processing is complete (if enabled)

## 7. Design Considerations:

   - Clear separation of concerns with Profile handling its own PostProcessor, OutputManager, and StreamingResultHandler
   - Profile manages its own state transitions and result processing, reducing ApplicationController involvement
   - Session IDs (UUIDs) provide a robust way to manage multiple concurrent recording/transcription jobs
   - Streaming and non-streaming modes are handled differently within the Profile class
   - ApplicationController focuses on high-level coordination and session management
   - Separate queues are created per profile to avoid ambiguity in audio data routing
   - UIManager provides a clean separation between UI logic and application logic
   - Qt dependencies are isolated within UIManager and EventBus
   - Use of EventBus for high-level communication and state changes, ensuring thread-safe event processing
   - Careful management of thread synchronization using Python's built-in thread-safe Queue
   - Dynamic configuration updates without requiring application restart
   - Support for both streaming and non-streaming transcription modes, configurable per profile
   - Implementation of voice activity detection (VAD) for certain recording modes
   - Potential for future expansion to support more complex scenarios or multiple simultaneous active profiles
   - Use of sentinel values in audio queues to simplify audio processing and state management in TranscriptionManager
