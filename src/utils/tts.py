"""
Text-to-Speech utilities
Enhanced with Vietnamese TTS support using HuggingFace models
"""

import io
from gtts import gTTS
import streamlit as st
from typing import Optional

# Try to import Vietnamese TTS components
try:
    from components.vietnamese_tts_components import (
        create_enhanced_audio_button,
        TTSPlayerManager
    )
    from src.config_manager import ConfigManager
    VIETNAMESE_TTS_AVAILABLE = True
except ImportError:
    VIETNAMESE_TTS_AVAILABLE = False


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


def create_audio_button(text: str, key: str, lang: str = 'vi', config_manager: ConfigManager = None) -> None:
    """
    Create a button that plays text when clicked
    Enhanced with Vietnamese TTS support
    
    Args:
        text: Text to convert to speech
        key: Unique key for the button
        lang: Language code
        config_manager: Configuration manager for enhanced TTS
    """
    
    # Use enhanced Vietnamese TTS if available and enabled
    if (VIETNAMESE_TTS_AVAILABLE and 
        config_manager and 
        config_manager.get_tts_enabled() and 
        lang == 'vi'):
        
        try:
            create_enhanced_audio_button(
                text=text,
                key=key,
                config_manager=config_manager,
                button_text="🔊 Nghe",
                show_controls=config_manager.get_tts_show_controls()
            )
            return
        except Exception as e:
            # Fallback to basic TTS if enhanced fails
            st.warning(f"Enhanced TTS failed, using fallback: {e}")
    
    # Fallback to basic gTTS
    if st.button("🔊 Nghe", key=key):
        speak(text, lang)


def create_smart_audio_button(
    text: str, 
    key: str, 
    config_manager: ConfigManager = None,
    button_text: str = "🔊 Nghe",
    show_generation_info: bool = False,
    auto_generate: bool = False
) -> Optional[str]:
    """
    Create smart audio button that chooses the best available TTS method
    
    Args:
        text: Text to convert to speech
        key: Unique key for the button
        config_manager: Configuration manager
        button_text: Custom button text
        show_generation_info: Show generation details
        auto_generate: Auto-generate audio in background
        
    Returns:
        Status message if any
    """
    
    if not text.strip():
        return None
    
    # Use Vietnamese TTS if available and configured
    if (VIETNAMESE_TTS_AVAILABLE and 
        config_manager and 
        config_manager.get_tts_enabled()):
        
        try:
            return create_enhanced_audio_button(
                text=text,
                key=key,
                config_manager=config_manager,
                button_text=button_text,
                show_controls=show_generation_info,
                auto_generate=auto_generate
            )
        except Exception as e:
            st.warning(f"Enhanced TTS failed: {e}")
    
    # Fallback to basic TTS
    if st.button(button_text, key=key):
        try:
            speak(text)
            return "Playing with basic TTS"
        except Exception as e:
            st.error(f"TTS error: {e}")
            return None
    
    return None


def get_tts_availability() -> dict:
    """Get TTS system availability information"""
    return {
        "basic_tts": True,  # gTTS is always available
        "vietnamese_tts": VIETNAMESE_TTS_AVAILABLE,
        "enhanced_features": VIETNAMESE_TTS_AVAILABLE
    }


def preload_tts_for_text(text: str, config_manager: ConfigManager = None) -> bool:
    """
    Preload TTS generation for text to improve performance
    
    Args:
        text: Text to preload
        config_manager: Configuration manager
        
    Returns:
        True if preloading was initiated
    """
    
    if not VIETNAMESE_TTS_AVAILABLE or not config_manager:
        return False
    
    try:
        # Initialize TTS manager if not exists
        if 'tts_manager' not in st.session_state:
            st.session_state.tts_manager = TTSPlayerManager(config_manager)
        
        # Generate in background
        import threading
        
        def background_generate():
            try:
                tts_manager = st.session_state.tts_manager
                if tts_manager.engine:
                    # Generate without storing in UI cache
                    result = tts_manager.engine.generate_speech(text)
                    return result is not None
            except Exception:
                return False
        
        thread = threading.Thread(target=background_generate)
        thread.start()
        
        return True
        
    except Exception:
        return False