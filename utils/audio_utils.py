# utils/audio_utils.py
import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def convert_to_pcm16k(input_bytes: bytes) -> str:
    """Converts any audio input to 16-bit PCM WAV @16kHz mono, returns path to new file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input_audio")
        output_path = os.path.join(tmpdir, "converted.wav")

        # Write uploaded file to disk
        with open(input_path, "wb") as f:
            f.write(input_bytes)

        # Run ffmpeg to convert to PCM WAV
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            output_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error("FFmpeg error:\n" + result.stderr.decode())
            raise ValueError("Failed to convert audio to PCM 16-bit WAV")

        # Read back the result to temp file outside context
        final_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with open(output_path, "rb") as f_in, open(final_temp.name, "wb") as f_out:
            f_out.write(f_in.read())

        return final_temp.name
