"""
Voice Cloning Module for Universal AI Agents
FIXED VERSION - Records for FULL 15 seconds regardless of pauses!
"""

import os
import json
import time
import requests
import speech_recognition as sr
from pydub import AudioSegment
import logging
import tempfile
import base64
import pyaudio
import wave
import threading

logger = logging.getLogger(__name__)

class VoiceCloner:
    def __init__(self):
        self.minimax_api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID", "1927290750123381288")
        
        if not self.minimax_api_key:
            logger.error("❌ MINIMAX_API_KEY not found!")
            self.mic = None
            self.recognizer = None
            return
        
        self.headers = {
            "Authorization": f"Bearer {self.minimax_api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize microphone components
        try:
            self.recognizer = sr.Recognizer()
            self.mic = sr.Microphone()
            self._setup_microphone()
        except Exception as e:
            logger.error(f"❌ Microphone initialization failed: {e}")
            self.mic = None
            self.recognizer = None

    def _setup_microphone(self):
        """Setup microphone for recording"""
        if not self.mic or not self.recognizer:
            return False
        
        try:
            with self.mic as source:
                logger.info("🎙️ Calibrating microphone for voice cloning...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            logger.info("✅ Microphone ready for voice cloning!")
            return True
        except Exception as e:
            logger.error(f"❌ Microphone setup failed: {e}")
            return False

    def record_fixed_duration(self, duration=15):
        """Record for EXACTLY the specified duration using PyAudio"""
        try:
            logger.info("🎙️ VOICE CLONING SETUP")
            logger.info("=" * 60)
            logger.info("📢 Please read this text SLOWLY and CLEARLY for 15 seconds:")
            logger.info("")
            logger.info("🗣️  'Hello! I'm setting up my AI voice assistant.")
            logger.info("    This voice cloning technology is amazing!")
            logger.info("    I'm creating my own personal AI agent.")
            logger.info("    This will be my unique digital voice.")
            logger.info("    The AI will speak with my voice patterns.")
            logger.info("    This is incredible technology in action.")
            logger.info("    My voice will be preserved digitally.")
            logger.info("    Keep talking, don't stop, this is fantastic!")
            logger.info("    We're making amazing progress here.")
            logger.info("    This voice cloning is truly remarkable!'")
            logger.info("")
            logger.info("⏰ CRITICAL: Keep talking for the FULL 15 seconds!")
            logger.info("🔄 Repeat the text if you finish early!")
            logger.info("🎯 Recording will start in 5 seconds...")
            
            # Countdown
            for i in range(5, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            # Audio recording parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Open stream
            stream = audio.open(format=FORMAT,
                              channels=CHANNELS,
                              rate=RATE,
                              input=True,
                              frames_per_buffer=CHUNK)
            
            logger.info("🔴 RECORDING NOW - SPEAK FOR FULL 15 SECONDS!")
            
            frames = []
            
            # Record with live countdown
            def countdown_display():
                for remaining in range(duration, 0, -1):
                    print(f"\\r⏰ Keep talking! {remaining} seconds remaining... ", end="", flush=True)
                    time.sleep(1)
                print("\\r✅ Recording complete! Processing...    ")
            
            # Start countdown thread
            countdown_thread = threading.Thread(target=countdown_display)
            countdown_thread.daemon = True
            countdown_thread.start()
            
            # Record for exact duration
            for i in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # Stop recording
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Wait for countdown to finish
            countdown_thread.join()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write WAV file
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Check file size
            file_size = os.path.getsize(temp_path)
            logger.info(f"📁 Audio file size: {file_size} bytes")
            logger.info(f"⏰ Recorded for exactly {duration} seconds!")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Fixed duration recording failed: {e}")
            return self.record_fallback_method(duration)

    def record_fallback_method(self, duration=15):
        """Fallback recording method"""
        if not self.mic or not self.recognizer:
            logger.error("❌ Microphone not available")
            return None
        
        logger.info("🔄 Using fallback recording method...")
        logger.info("🔴 RECORDING NOW - SPEAK CONTINUOUSLY!")
        
        try:
            self.recognizer.energy_threshold = 50
            self.recognizer.dynamic_energy_threshold = False
            self.recognizer.pause_threshold = 2.0
            self.recognizer.phrase_threshold = 0.1
            self.recognizer.non_speaking_duration = 1.5
            
            with self.mic as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=duration + 5,
                    phrase_time_limit=duration
                )
            
            logger.info("✅ Fallback recording complete!")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                with open(temp_path, "wb") as f:
                    f.write(audio.get_wav_data())
            
            file_size = os.path.getsize(temp_path)
            logger.info(f"📁 Audio file size: {file_size} bytes")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Fallback recording failed: {e}")
            return None

    def upload_audio_file(self, audio_file_path):
        """Upload audio file to MiniMax"""
        try:
            logger.info("📤 Uploading audio file to MiniMax...")
            
            upload_url = f"https://api.minimaxi.chat/v1/files/upload?GroupId={self.group_id}"
            
            upload_headers = {
                "Authorization": f"Bearer {self.minimax_api_key}"
            }
            
            data = {'purpose': 'voice_clone'}
            
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': ('audio.wav', audio_file, 'audio/wav')}
                response = requests.post(upload_url, headers=upload_headers, data=data, files=files, timeout=60)
            
            logger.info(f"📡 Upload response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                file_id = None
                if 'file' in result and 'file_id' in result['file']:
                    file_id = result['file']['file_id']
                elif 'file_id' in result:
                    file_id = result['file_id']
                
                if file_id:
                    logger.info(f"✅ File uploaded successfully! File ID: {file_id}")
                    return file_id
                else:
                    logger.error(f"❌ No file_id in response: {result}")
                    return None
            else:
                logger.error(f"❌ File upload failed: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"❌ File upload error: {e}")
            return None

    def clone_voice_with_minimax(self, file_id):
        """Clone voice using MiniMax API"""
        try:
            logger.info("🧬 Cloning your voice with MiniMax...")
            
            clone_url = f"https://api.minimaxi.chat/v1/voice_clone?GroupId={self.group_id}"
            voice_id = f"agent{int(time.time())}"
            
            payload = {
                "file_id": file_id,
                "voice_id": voice_id,
                "noise_reduction": True,
                "need_volume_normalization": True
            }
            
            logger.info(f"🚀 Cloning voice with ID: {voice_id}")
            
            response = requests.post(clone_url, headers=self.headers, json=payload, timeout=120)
            
            logger.info(f"📡 Clone response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'base_resp' in result:
                    base_resp = result['base_resp']
                    if base_resp.get('status_code') == 0 and base_resp.get('status_msg') == 'success':
                        logger.info(f"✅ Voice cloned successfully! Voice ID: {voice_id}")
                        return voice_id
                    elif base_resp.get('status_code') == 2037:
                        logger.error("❌ Voice duration too short!")
                        return None
                    else:
                        logger.error(f"❌ Clone failed: {base_resp}")
                        return None
                else:
                    logger.error(f"❌ Unexpected response format: {result}")
                    return None
            else:
                logger.error(f"❌ Voice cloning failed: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Voice cloning error: {e}")
            return None

    def test_minimax_connection(self):
        """Test MiniMax API connection"""
        try:
            logger.info("🔍 Testing MiniMax API connection...")
            
            test_url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
            
            test_payload = {
                "model": "speech-01-turbo",
                "text": "test",
                "stream": False,
                "voice_setting": {
                    "voice_id": "female-tianmei-jingpin",
                    "speed": 1.0,
                    "vol": 1.0,
                    "pitch": 0
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3"
                }
            }
            
            response = requests.post(test_url, headers=self.headers, json=test_payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ MiniMax API connection successful!")
                return True
            else:
                logger.warning(f"⚠️ Unexpected response: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def setup_voice_cloning(self):
        """Main voice cloning setup"""
        if not self.minimax_api_key:
            logger.error("❌ MINIMAX_API_KEY not found - skipping voice cloning")
            return None
        
        if not self.test_minimax_connection():
            logger.error("❌ MiniMax API connection failed - skipping voice cloning")
            return None
        
        if not self.mic or not self.recognizer:
            logger.error("❌ Microphone not available - skipping voice cloning")
            return None
        
        logger.info("\\n🎙️ Setting up voice cloning...")
        
        audio_file = self.record_fixed_duration(15)
        if not audio_file:
            logger.error("❌ Failed to record voice sample")
            return None
        
        try:
            file_id = self.upload_audio_file(audio_file)
            if not file_id:
                logger.error("❌ Failed to upload audio file")
                return None
            
            cloned_voice_id = self.clone_voice_with_minimax(file_id)
            
            if cloned_voice_id:
                logger.info("🎉 SUCCESS! Your voice has been cloned!")
                return cloned_voice_id
            else:
                logger.error("❌ Voice cloning failed")
                return None
            
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        
        return None