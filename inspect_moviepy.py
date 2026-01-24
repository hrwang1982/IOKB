from moviepy import VideoFileClip
import inspect

try:
    # Create a dummy clip to access the audio write method
    # or just inspect the base class if possible
    from moviepy.audio.AudioClip import AudioClip
    
    sig = inspect.signature(AudioClip.write_audiofile)
    print(f"AudioClip.write_audiofile signature: {sig}")
except Exception as e:
    print(f"Error inspecting: {e}")

try:
    # Also check if it's different on the AudioFileClip attached to VideoFileClip
    # We can't easily create a clip without a file, so we'll trust the class inspection
    pass
except Exception as e:
    pass
