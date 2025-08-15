"""
Vietnamese TTS UI Components
Enhanced audio player and TTS controls for Vietnamese travel assistant
"""

import base64
import io
import streamlit as st
from typing import Optional, Dict, Any, Callable
import time
import threading
from pathlib import Path

# Import TTS engine
try:
    from src.vietnamese_tts_engine import (
        VietnameseTTSEngine, TTSConfig, TTSModel, TTSResult
    )
    TTS_AVAILABLE = True
except ImportError as e:
    TTS_AVAILABLE = False
    print(f"Vietnamese TTS not available: {e}")

# Always import ConfigManager
from src.config_manager import ConfigManager


class TTSPlayerManager:
    """Manages TTS playback and UI state"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._engine = None
        self._generation_cache = {}
        
        # Initialize session state
        if 'tts_player_state' not in st.session_state:
            st.session_state.tts_player_state = {
                'current_audio': None,
                'generation_status': {},
                'last_generated': None,
                'settings': {
                    'speed': 1.0,
                    'pitch': 1.0,
                    'model': 'facebook/mms-tts-vie',
                    'auto_play': False
                }
            }
    
    @property
    def engine(self) -> Optional[VietnameseTTSEngine]:
        """Get or create TTS engine instance"""
        if not TTS_AVAILABLE:
            return None
            
        if self._engine is None and self.config_manager.get_tts_enabled():
            try:
                # Create TTS config from ConfigManager
                tts_config = TTSConfig(
                    primary_model=TTSModel(self.config_manager.get_tts_primary_model()),
                    voice_speed=self.config_manager.get_tts_voice_speed(),
                    voice_pitch=self.config_manager.get_tts_voice_pitch(),
                    audio_quality=self.config_manager.get_tts_audio_quality(),
                    enable_cache=self.config_manager.get_tts_cache_enabled(),
                    cache_dir="audio_cache",
                    max_cache_size_mb=self.config_manager.get_tts_cache_size_mb(),
                    enable_async=self.config_manager.get_tts_async_enabled(),
                    gpu_enabled=self.config_manager.get_tts_gpu_enabled()
                )
                
                self._engine = VietnameseTTSEngine(tts_config)
                
            except Exception as e:
                st.error(f"Failed to initialize TTS engine: {e}")
                return None
        
        return self._engine
    
    def generate_audio(self, text: str, key: str, callback: Callable = None) -> Optional[bytes]:
        """Generate audio for text with caching"""
        if not self.engine:
            return None
        
        # Check if generation is in progress
        if key in st.session_state.tts_player_state['generation_status']:
            return None
        
        # Check cache first
        if key in self._generation_cache:
            return self._generation_cache[key]
        
        try:
            # Mark as generating
            st.session_state.tts_player_state['generation_status'][key] = 'generating'
            
            # Get current model from settings
            current_model = st.session_state.tts_player_state['settings']['model']
            model_enum = TTSModel(current_model) if current_model != 'gtts' else TTSModel.GOOGLE_TTS
            
            # Generate speech
            result = self.engine.generate_speech(text, model_enum)
            
            # Cache result
            self._generation_cache[key] = result.audio_data
            
            # Update status
            st.session_state.tts_player_state['generation_status'][key] = 'completed'
            st.session_state.tts_player_state['last_generated'] = {
                'key': key,
                'model': result.model_used.value,
                'time': result.generation_time,
                'cache_hit': result.cache_hit
            }
            
            if callback:
                callback(result)
            
            return result.audio_data
            
        except Exception as e:
            st.session_state.tts_player_state['generation_status'][key] = f'error: {str(e)}'
            st.error(f"TTS generation failed: {e}")
            return None
    
    def clear_cache(self):
        """Clear generation cache"""
        self._generation_cache.clear()
        if self.engine:
            self.engine.clear_cache()
        st.session_state.tts_player_state['generation_status'].clear()


def create_enhanced_audio_button(
    text: str, 
    key: str, 
    config_manager: ConfigManager,
    button_text: str = "🔊 Nghe",
    show_controls: bool = True,
    auto_generate: bool = False
) -> Optional[str]:
    """
    Create enhanced audio button with TTS capabilities
    
    Args:
        text: Text to convert to speech
        key: Unique key for the component
        config_manager: Configuration manager instance
        button_text: Text for the play button
        show_controls: Whether to show additional controls
        auto_generate: Whether to auto-generate audio
        
    Returns:
        Status message if any
    """
    
    if not TTS_AVAILABLE or not config_manager.get_tts_enabled():
        # Fallback to basic TTS
        if st.button(button_text, key=key):
            try:
                from src.utils.tts import speak
                speak(text)
                return "Playing with basic TTS"
            except Exception as e:
                st.error(f"TTS error: {e}")
                return None
        return None
    
    # Initialize TTS manager
    if 'tts_manager' not in st.session_state:
        st.session_state.tts_manager = TTSPlayerManager(config_manager)
    
    tts_manager = st.session_state.tts_manager
    
    # Create container for audio controls
    audio_container = st.container()
    
    with audio_container:
        # Main control row
        control_cols = st.columns([1, 3, 1] if show_controls else [1, 4])
        
        with control_cols[0]:
            # Play button
            if st.button(button_text, key=f"{key}_play"):
                audio_data = tts_manager.generate_audio(text, key)
                if audio_data:
                    # Create audio player
                    b64_audio = base64.b64encode(audio_data).decode()
                    audio_html = f"""
                    <audio controls autoplay style="width: 100%;">
                        <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
                        Your browser does not support the audio element.
                    </audio>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)
                    return "Audio generated successfully"
        
        if show_controls and len(control_cols) > 2:
            with control_cols[1]:
                # Status display
                status = st.session_state.tts_player_state['generation_status'].get(key, 'ready')
                if status == 'generating':
                    st.info("🔄 Generating audio...")
                elif status == 'completed':
                    last_gen = st.session_state.tts_player_state.get('last_generated', {})
                    if last_gen.get('key') == key:
                        cache_status = "💾 Cached" if last_gen.get('cache_hit') else "🆕 Generated"
                        model_name = last_gen.get('model', 'Unknown').split('/')[-1]
                        st.success(f"{cache_status} • {model_name} • {last_gen.get('time', 0):.1f}s")
                elif isinstance(status, str) and status.startswith('error'):
                    st.error(f"❌ {status}")
            
            with control_cols[2]:
                # Settings button
                if st.button("⚙️", key=f"{key}_settings", help="TTS Settings"):
                    st.session_state[f"{key}_show_settings"] = not st.session_state.get(f"{key}_show_settings", False)
        
        # Settings panel
        if show_controls and st.session_state.get(f"{key}_show_settings", False):
            with st.expander("🎛️ TTS Settings", expanded=True):
                settings_cols = st.columns(2)
                
                with settings_cols[0]:
                    # Model selection
                    available_models = [
                        ("Facebook MMS", "facebook/mms-tts-vie"),
                        ("Zalopay TTS", "zalopay/vietnamese-tts"),
                        ("F5-TTS", "hynt/F5-TTS-Vietnamese-100h"),
                        ("Google TTS", "gtts")
                    ]
                    
                    current_model = st.session_state.tts_player_state['settings']['model']
                    model_names = [name for name, value in available_models]
                    model_values = [value for name, value in available_models]
                    
                    try:
                        current_index = model_values.index(current_model)
                    except ValueError:
                        current_index = 0
                    
                    selected_model = st.selectbox(
                        "Model",
                        options=model_names,
                        index=current_index,
                        key=f"{key}_model_select"
                    )
                    
                    # Update model setting
                    new_model_value = model_values[model_names.index(selected_model)]
                    if new_model_value != current_model:
                        st.session_state.tts_player_state['settings']['model'] = new_model_value
                        # Clear cache for this key to force regeneration
                        if key in st.session_state.tts_player_state['generation_status']:
                            del st.session_state.tts_player_state['generation_status'][key]
                
                with settings_cols[1]:
                    # Voice controls
                    speed = st.slider(
                        "Speed",
                        min_value=0.5,
                        max_value=2.0,
                        value=st.session_state.tts_player_state['settings']['speed'],
                        step=0.1,
                        key=f"{key}_speed"
                    )
                    
                    if speed != st.session_state.tts_player_state['settings']['speed']:
                        st.session_state.tts_player_state['settings']['speed'] = speed
                        if tts_manager.engine:
                            tts_manager.engine.set_voice_config(speed=speed)
                
                # Cache management
                cache_cols = st.columns([2, 1, 1])
                with cache_cols[0]:
                    if tts_manager.engine:
                        cache_stats = tts_manager.engine.get_cache_stats()
                        if cache_stats.get('enabled'):
                            st.caption(f"Cache: {cache_stats['files']} files, {cache_stats['size_mb']:.1f}MB")
                
                with cache_cols[1]:
                    if st.button("🗑️ Clear Cache", key=f"{key}_clear_cache"):
                        tts_manager.clear_cache()
                        st.success("Cache cleared")
                
                with cache_cols[2]:
                    if st.button("❌ Close", key=f"{key}_close_settings"):
                        st.session_state[f"{key}_show_settings"] = False
                        st.rerun()
    
    # Auto-generate if requested
    if auto_generate and key not in st.session_state.tts_player_state['generation_status']:
        # Generate audio in background
        def auto_gen_callback(result):
            if result:
                st.session_state.tts_player_state['current_audio'] = result.audio_data
        
        threading.Thread(
            target=lambda: tts_manager.generate_audio(text, key, auto_gen_callback)
        ).start()
    
    return None


def create_tts_settings_panel(config_manager: ConfigManager) -> bool:
    """
    Create TTS settings panel for global configuration
    
    Returns:
        True if settings were updated
    """
    
    if not TTS_AVAILABLE:
        st.warning("Vietnamese TTS is not available. Please install required dependencies.")
        return False
    
    st.subheader("🎤 Vietnamese Text-to-Speech Settings")
    
    settings_updated = False
    
    # Enable/Disable TTS
    tts_enabled = st.checkbox(
        "Enable Vietnamese TTS",
        value=config_manager.get_tts_enabled(),
        help="Enable high-quality Vietnamese text-to-speech"
    )
    
    if tts_enabled != config_manager.get_tts_enabled():
        config_manager.update_tts_config({'enable_tts': tts_enabled})
        settings_updated = True
    
    if tts_enabled:
        # Model configuration
        st.markdown("### 🤖 Model Configuration")
        
        model_cols = st.columns(2)
        
        with model_cols[0]:
            # Primary model selection
            model_options = {
                "Facebook MMS (Recommended)": "facebook/mms-tts-vie",
                "Zalopay TTS (High Quality)": "zalopay/vietnamese-tts",
                "F5-TTS (Fast)": "hynt/F5-TTS-Vietnamese-100h",
                "VietTTS (Advanced)": "dangvansam/viet-tts"
            }
            
            current_primary = config_manager.get_tts_primary_model()
            primary_display = next(
                (k for k, v in model_options.items() if v == current_primary),
                "Facebook MMS (Recommended)"
            )
            
            selected_primary = st.selectbox(
                "Primary Model",
                options=list(model_options.keys()),
                index=list(model_options.keys()).index(primary_display),
                help="Primary model for TTS generation"
            )
            
            new_primary = model_options[selected_primary]
            if new_primary != current_primary:
                config_manager.update_tts_config({'tts_primary_model': new_primary})
                settings_updated = True
        
        with model_cols[1]:
            # Quality settings
            quality_options = ["low", "medium", "high"]
            current_quality = config_manager.get_tts_audio_quality()
            
            selected_quality = st.selectbox(
                "Audio Quality",
                options=quality_options,
                index=quality_options.index(current_quality),
                help="Higher quality uses more resources"
            )
            
            if selected_quality != current_quality:
                config_manager.update_tts_config({'tts_audio_quality': selected_quality})
                settings_updated = True
        
        # Voice settings
        st.markdown("### 🎵 Voice Settings")
        
        voice_cols = st.columns(2)
        
        with voice_cols[0]:
            voice_speed = st.slider(
                "Voice Speed",
                min_value=0.5,
                max_value=2.0,
                value=config_manager.get_tts_voice_speed(),
                step=0.1,
                help="Adjust speaking speed"
            )
            
            if voice_speed != config_manager.get_tts_voice_speed():
                config_manager.update_tts_config({'tts_voice_speed': voice_speed})
                settings_updated = True
        
        with voice_cols[1]:
            voice_pitch = st.slider(
                "Voice Pitch",
                min_value=0.5,
                max_value=2.0,
                value=config_manager.get_tts_voice_pitch(),
                step=0.1,
                help="Adjust voice pitch"
            )
            
            if voice_pitch != config_manager.get_tts_voice_pitch():
                config_manager.update_tts_config({'tts_voice_pitch': voice_pitch})
                settings_updated = True
        
        # Performance settings
        st.markdown("### ⚡ Performance Settings")
        
        perf_cols = st.columns(2)
        
        with perf_cols[0]:
            cache_enabled = st.checkbox(
                "Enable Audio Caching",
                value=config_manager.get_tts_cache_enabled(),
                help="Cache generated audio for faster playback"
            )
            
            if cache_enabled != config_manager.get_tts_cache_enabled():
                config_manager.update_tts_config({'tts_enable_cache': cache_enabled})
                settings_updated = True
            
            if cache_enabled:
                cache_size = st.number_input(
                    "Cache Size (MB)",
                    min_value=50,
                    max_value=2000,
                    value=config_manager.get_tts_cache_size_mb(),
                    step=50,
                    help="Maximum cache size in megabytes"
                )
                
                if cache_size != config_manager.get_tts_cache_size_mb():
                    config_manager.update_tts_config({'tts_cache_size_mb': cache_size})
                    settings_updated = True
        
        with perf_cols[1]:
            gpu_enabled = st.checkbox(
                "Use GPU Acceleration",
                value=config_manager.get_tts_gpu_enabled(),
                help="Use GPU for faster model inference (if available)"
            )
            
            if gpu_enabled != config_manager.get_tts_gpu_enabled():
                config_manager.update_tts_config({'tts_gpu_enabled': gpu_enabled})
                settings_updated = True
            
            async_enabled = st.checkbox(
                "Asynchronous Generation",
                value=config_manager.get_tts_async_enabled(),
                help="Generate audio in background for better performance"
            )
            
            if async_enabled != config_manager.get_tts_async_enabled():
                config_manager.update_tts_config({'tts_enable_async': async_enabled})
                settings_updated = True
        
        # UI settings
        st.markdown("### 🎨 Interface Settings")
        
        ui_cols = st.columns(2)
        
        with ui_cols[0]:
            show_controls = st.checkbox(
                "Show TTS Controls",
                value=config_manager.get_tts_show_controls(),
                help="Show additional TTS controls in chat"
            )
            
            if show_controls != config_manager.get_tts_show_controls():
                config_manager.update_tts_config({'tts_show_controls': show_controls})
                settings_updated = True
        
        with ui_cols[1]:
            auto_play = st.checkbox(
                "Auto-play Audio",
                value=config_manager.get_tts_auto_play(),
                help="Automatically play generated audio"
            )
            
            if auto_play != config_manager.get_tts_auto_play():
                config_manager.update_tts_config({'tts_auto_play': auto_play})
                settings_updated = True
        
        # Test TTS
        st.markdown("### 🧪 Test TTS")
        
        test_text = st.text_input(
            "Test Text",
            value="Xin chào! Đây là hệ thống Text-to-Speech tiếng Việt của trợ lý du lịch.",
            help="Enter Vietnamese text to test TTS"
        )
        
        if test_text and st.button("🎵 Test TTS", key="test_tts_button"):
            create_enhanced_audio_button(
                text=test_text,
                key="tts_test",
                config_manager=config_manager,
                button_text="🔊 Play Test",
                show_controls=True
            )
    
    if settings_updated:
        st.success("TTS settings updated successfully!")
        
        # Clear any existing TTS engine to force reload with new settings
        if 'tts_manager' in st.session_state:
            st.session_state.tts_manager._engine = None
    
    return settings_updated


def render_audio_download_button(audio_data: bytes, filename: str, key: str):
    """Render download button for audio data"""
    if audio_data:
        st.download_button(
            label="💾 Download Audio",
            data=audio_data,
            file_name=f"{filename}.wav",
            mime="audio/wav",
            key=key
        )


def get_tts_status_info(config_manager: ConfigManager) -> Dict[str, Any]:
    """Get current TTS system status information"""
    
    if not TTS_AVAILABLE:
        return {
            "available": False,
            "error": "TTS dependencies not installed"
        }
    
    status = {
        "available": True,
        "enabled": config_manager.get_tts_enabled(),
        "primary_model": config_manager.get_tts_primary_model(),
        "cache_enabled": config_manager.get_tts_cache_enabled(),
        "gpu_enabled": config_manager.get_tts_gpu_enabled()
    }
    
    # Check if TTS manager is initialized
    if 'tts_manager' in st.session_state:
        tts_manager = st.session_state.tts_manager
        if tts_manager.engine:
            try:
                cache_stats = tts_manager.engine.get_cache_stats()
                status["cache_stats"] = cache_stats
                status["models_loaded"] = len(tts_manager.engine._loaded_models)
            except Exception as e:
                status["engine_error"] = str(e)
    
    return status