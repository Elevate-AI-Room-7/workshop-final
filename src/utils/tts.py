"""
Text-to-Speech utilities
"""

import io
from gtts import gTTS
import streamlit as st


def speak(text: str, lang: str = 'vi') -> None:
    """
    Convert text to speech and play in Streamlit
    
    Args:
        text: Text to convert to speech
        lang: Language code (default: 'vi' for Vietnamese)
    """
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        st.audio(mp3_fp, format='audio/mp3')
    except Exception as e:
        st.error(f"❌ Lỗi Text-to-Speech: {e}")


def create_audio_button(text: str, key: str, lang: str = 'vi') -> None:
    """
    Create a button that plays text when clicked
    
    Args:
        text: Text to convert to speech
        key: Unique key for the button
        lang: Language code
    """
    if st.button("🔊 Nghe", key=key):
        speak(text, lang)