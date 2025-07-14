import whisper
import sounddevice as sd
import wave
import numpy as np
import keyboard
import time

class SpeechToTextManager:
    def __init__(self):
        # Load the Whisper model (you can choose 'tiny', 'base', 'small', 'medium', 'large')
        self.model = whisper.load_model("base")

    def save_audio(self, filename, audio_data, sample_rate=16000):
        # Save recorded audio to WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

    def speechtotext_from_mic(self):
        # Record audio
        sample_rate = 16000
        duration = 5  # seconds
        print("Speak into your microphone.")
        
        audio_data = sd.rec(int(sample_rate * duration), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype=np.int16)
        sd.wait()
        
        # Save to temporary file
        temp_file = "temp_recording.wav"
        self.save_audio(temp_file, audio_data)
        
        # Transcribe using Whisper
        result = self.model.transcribe(temp_file)
        text_result = result["text"].strip()
        
        print(f"We got the following text: {text_result}")
        return text_result

    def speechtotext_from_file(self, filename):
        print("Processing the file...")
        result = self.model.transcribe(filename)
        text_result = result["text"].strip()
        
        print(f"Recognized: \n{text_result}")
        return text_result

    def speechtotext_from_mic_continuous(self, stop_key='p'):
        print('Continuous Speech Recognition is now running. Press "p" to stop.')
        all_results = []
        
        # Parameters for recording
        sample_rate = 16000
        chunk_duration = 5  # seconds
        
        while True:
            if keyboard.is_pressed(stop_key):
                print("\nStopping speech recognition\n")
                break
                
            print("\nListening...")
            # Record audio chunk
            audio_data = sd.rec(int(sample_rate * chunk_duration), 
                              samplerate=sample_rate, 
                              channels=1, 
                              dtype=np.int16)
            sd.wait()
            
            # Save to temporary file
            temp_file = "temp_recording.wav"
            self.save_audio(temp_file, audio_data)
            
            # Transcribe
            result = self.model.transcribe(temp_file)
            text_result = result["text"].strip()
            
            if text_result:
                print(f"Recognized: {text_result}")
                all_results.append(text_result)
        
        final_result = " ".join(all_results).strip()
        print(f"\n\nFinal result:\n{final_result}\n")
        return final_result


# Tests
if __name__ == '__main__':
    TEST_FILE = "path/to/your/audio/file.wav"
    
    speechtotext_manager = SpeechToTextManager()

    while True:
        #result = speechtotext_manager.speechtotext_from_mic()
        #result = speechtotext_manager.speechtotext_from_file(TEST_FILE)
        result = speechtotext_manager.speechtotext_from_mic_continuous()
        print(f"\n\nHERE IS THE RESULT:\n{result}")
        time.sleep(60)
