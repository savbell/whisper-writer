1. Core Components:

   a. AudioManager:
      - Manages its own thread, running for the duration of the program
      - Handles audio recording based on triggered shortcuts and recording modes
      - Supports both streaming and non-streaming modes
      - In streaming mode, continuously emits small audio chunks (e.g., 200ms) to a queue
      - In non-streaming mode, collects all audio before sending it to the queue
      - Uses session IDs to identify and manage individual recording sessions
      - Implements voice activity detection (VAD) for certain recording modes

   b. Profile:
      - Encapsulates related components and settings:
        - TranscriptionManager: Handles transcription for a specific backend, manages its own thread
        - PostProcessor: Applies post-processing to transcribed text
        - OutputManager: Handles output operations specific to the profile
      - Associated with a specific activation shortcut
      - Maintains its state (IDLE, RECORDING, TRANSCRIBING, STREAMING)
      - Configurable for streaming or non-streaming transcription mode

   c. InputManager:
      - Runs on the main thread
      - Handles all input events (keyboard shortcuts, GUI interactions)
      - Maps shortcuts to specific profiles

   d. ConfigManager:
      - Manages global options and profile-specific configurations
      - Supports dynamic configuration updates
      - Notifies components of relevant config changes via events
      - Implemented as a static class with class methods

   e. UIManager:
      - Manages all UI components:
        - MainWindow: Displayed only at program launch for initial setup
        - SettingsWindow: Accessible via tray icon menu for configuration
        - StatusWindow: Optional window that appears during recording and transcription
        - TrayIconManager: Manages the system tray icon and its menu
      - Handles UI-related logic and user interactions
      - Encapsulates all Qt-specific code except for EventBus

2. Main Application Flow:

   a. ApplicationController:
      - Runs on the main thread
      - Central coordinator for all core components
      - Manages the lifecycle of the application and profiles
      - Handles high-level logic for different operation modes (streaming and non-streaming)
      - Manages session IDs for each recording/transcription job
      - Activates/deactivates recording and transcription based on shortcuts and session IDs
      - Receives final transcription results and routes them back to the appropriate Profile for output

3. Communication and Event Handling:

   a. EventBus:
      - Central event system for inter-component communication
      - Uses Qt signals to ensure events are processed on the main thread
      - Provides subscribe/unsubscribe functionality for event handling

   b. Queue:
      - Python's built-in Queue class is used, which is thread-safe by design
      - A separate queue is created for each profile to manage audio data
      - Used for passing audio data between AudioManager and TranscriptionManager within a profile

4. Threading Model:

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

5. Session Management:

   - Each recording/transcription job is assigned a unique session ID (UUID)
   - Session IDs are used to track the lifecycle of each job from recording through transcription
   - ApplicationController maintains a mapping between session IDs and profiles
   - AudioManager and TranscriptionManager use session IDs to manage concurrent jobs

6. Workflow:

   - Program launches, creates QApplication instance
   - main() initializes UIManager, EventBus, ConfigManager, and ApplicationController
   - UIManager displays MainWindow for initial setup
   - After setup, MainWindow closes and TrayIconManager creates system tray icon
   - ApplicationController initializes AudioManager, InputManager, and profiles based on configuration
   - Profile(s) initializes its TranscriptionManager and OutputManager
   - Audio and Transcription threads are started and run continuously
   - InputManager listens for configured shortcuts
   - When a shortcut is triggered, InputManager notifies ApplicationController via EventBus
   - ApplicationController identifies the corresponding profile
   - ApplicationController generates a new session ID and starts recording via AudioManager
   - UIManager shows/updates StatusWindow if enabled
   - AudioManager sends audio data to the profile's queue, either in chunks (streaming) or complete (non-streaming)
   - TranscriptionManager processes audio from the profile's queue based on the profile's configuration
   - TranscriptionManager sends results (partial or final) to the Profile
   - Profile routes the results to its PostProcessor
   - Profile sends processed results to ApplicationController (for final results only)
   - ApplicationController routes final results back to Profile.output()
   - Profile's OutputManager receives processed results and performs necessary actions
   - UIManager updates with partial results in streaming mode, or final results in non-streaming mode
   - When transcription is complete, ApplicationController cleans up the session
   - UIManager hides StatusWindow when processing is complete (if enabled)

7. Design Considerations:

   - UIManager, EventBus, and ConfigManager are initialized in main() to ensure Qt dependencies are isolated in UIManager
   - Separate queues are created per profile to avoid ambiguity in audio data routing
   - Clear separation of concerns with Profile handling its own PostProcessor and OutputManager
   - Session IDs (UUIDs) provide a robust way to manage multiple concurrent recording/transcription jobs
   - UIManager provides a clean separation between UI logic and application logic
   - Qt dependencies are isolated within UIManager and EventBus
   - System tray icon provides easy access to settings and profile management after initial setup
   - Audio and Transcription threads run continuously, improving responsiveness when activated
   - Profiles provide a flexible way to group related settings and components
   - Use of EventBus for high-level communication and state changes, ensuring thread-safe event processing
   - Direct function calls for straightforward, synchronous operations within components
   - Careful management of thread synchronization using Python's built-in thread-safe Queue
   - Dynamic configuration updates without requiring application restart
   - Clear separation of concerns between components while centralizing coordination in ApplicationController
   - Ability to switch between profiles on-the-fly using shortcuts
   - Profile states (IDLE, RECORDING, TRANSCRIBING, STREAMING) provide clear representation of current activity
   - Support for both streaming and non-streaming transcription modes, configurable per profile
   - Efficient handling of audio data using thread-safe queues
   - Implementation of voice activity detection (VAD) for certain recording modes
   - Potential for future expansion to support more complex scenarios or multiple simultaneous active profiles
