import wave
import pyaudio
import os


def play_wav(file_path):
    if not os.path.exists(file_path):
        return
    # Open the WAV file
    with wave.open(file_path, 'rb') as wf:
        # Create an interface to PortAudio
        p = pyaudio.PyAudio()

        # Open a .Stream object to write the WAV file to
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        # Read data in chunks
        chunk_size = 1024
        data = wf.readframes(chunk_size)

        # Play the sound by writing audio data to the stream
        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)

        # Close and terminate the stream
        stream.close()
        p.terminate()
