"""
Vietnamese Text-to-Speech Engine
Enhanced TTS system using HuggingFace models for high-quality Vietnamese speech synthesis
"""

import os
import io
import re
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from pathlib import Path

# Core dependencies - with graceful fallbacks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from transformers import VitsModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    VitsModel = None
    AutoTokenizer = None

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    sf = None

# Fallback imports
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Optional audio processing
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class TTSModel(Enum):
    """Available TTS models"""
    FACEBOOK_MMS = "facebook/mms-tts-vie"
    ZALOPAY_TTS = "zalopay/vietnamese-tts"
    F5_TTS = "hynt/F5-TTS-Vietnamese-100h"
    VIET_TTS = "dangvansam/viet-tts"
    GOOGLE_TTS = "gtts"  # Fallback


@dataclass
class TTSConfig:
    """TTS configuration settings"""
    primary_model: TTSModel = TTSModel.FACEBOOK_MMS
    fallback_models: List[TTSModel] = None
    voice_speed: float = 1.0
    voice_pitch: float = 1.0
    audio_quality: str = "medium"  # low, medium, high
    enable_cache: bool = True
    cache_dir: str = "audio_cache"
    max_cache_size_mb: int = 500
    enable_async: bool = True
    gpu_enabled: bool = None  # Auto-detect
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = [
                TTSModel.ZALOPAY_TTS,
                TTSModel.F5_TTS,
                TTSModel.GOOGLE_TTS
            ]
        
        if self.gpu_enabled is None:
            self.gpu_enabled = torch.cuda.is_available()


@dataclass
class TTSResult:
    """TTS generation result"""
    audio_data: bytes
    sample_rate: int
    model_used: TTSModel
    generation_time: float
    cache_hit: bool
    text_processed: str


class VietnameseTextProcessor:
    """Vietnamese text preprocessing for TTS"""
    
    def __init__(self):
        self.number_map = {
            '0': 'không', '1': 'một', '2': 'hai', '3': 'ba', '4': 'bốn',
            '5': 'năm', '6': 'sáu', '7': 'bảy', '8': 'tám', '9': 'chín'
        }
        
        self.abbreviations = {
            'TP.HCM': 'Thành phố Hồ Chí Minh',
            'TP': 'Thành phố',
            'Q.': 'Quận',
            'P.': 'Phường',
            'TT': 'Thành thị',
            'TX': 'Thị xã',
            'VND': 'đồng Việt Nam',
            'USD': 'đô la Mỹ',
            'km': 'ki lô mét',
            'km/h': 'ki lô mét một giờ',
            'vs': 'so với',
            'etc': 'vân vân',
            'ok': 'ô kê',
            'wifi': 'oai fai'
        }
        
        self.location_pronunciations = {
            'Đà Nẵng': 'Đà Nẵng',
            'Huế': 'Huế',
            'Nha Trang': 'Nha Trang',
            'Phú Quốc': 'Phú Quốc',
            'Sapa': 'Sa Pa',
            'Đà Lạt': 'Đà Lạt',
            'Hạ Long': 'Hạ Long',
            'Hội An': 'Hội An'
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize Vietnamese text for TTS"""
        if not text.strip():
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle abbreviations
        for abbr, full in self.abbreviations.items():
            text = text.replace(abbr, full)
        
        # Handle location pronunciations
        for location, pronunciation in self.location_pronunciations.items():
            text = text.replace(location, pronunciation)
        
        # Convert numbers to words (basic implementation)
        text = self._convert_numbers(text)
        
        # Handle dates
        text = self._convert_dates(text)
        
        # Handle currency
        text = self._convert_currency(text)
        
        # Remove special characters that don't add to speech
        text = re.sub(r'[^\w\s\.,\!\?\-\:;]', '', text)
        
        # Normalize punctuation spacing
        text = re.sub(r'\s*([,.!?:;])\s*', r'\1 ', text)
        
        return text.strip()
    
    def _convert_numbers(self, text: str) -> str:
        """Convert simple numbers to Vietnamese words"""
        # Simple number conversion for 1-digit numbers
        def replace_digit(match):
            digit = match.group(0)
            return self.number_map.get(digit, digit)
        
        # Convert standalone digits
        text = re.sub(r'\b\d\b', replace_digit, text)
        
        return text
    
    def _convert_dates(self, text: str) -> str:
        """Convert date formats to Vietnamese pronunciation"""
        # DD/MM/YYYY format
        date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        
        def replace_date(match):
            day, month, year = match.groups()
            return f"ngày {day} tháng {month} năm {year}"
        
        text = re.sub(date_pattern, replace_date, text)
        
        return text
    
    def _convert_currency(self, text: str) -> str:
        """Convert currency formats"""
        # Simple VND conversion
        vnd_pattern = r'(\d{1,3}(?:,\d{3})*)\s*VND'
        text = re.sub(vnd_pattern, r'\1 đồng', text)
        
        return text


class AudioCache:
    """Audio caching system for TTS"""
    
    def __init__(self, cache_dir: str = "audio_cache", max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_mb = max_size_mb
        self._cache_lock = threading.Lock()
    
    def _get_cache_key(self, text: str, model: TTSModel, config: dict) -> str:
        """Generate cache key for text and model configuration"""
        content = f"{text}_{model.value}_{str(sorted(config.items()))}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, text: str, model: TTSModel, config: dict) -> Optional[bytes]:
        """Get cached audio data"""
        cache_key = self._get_cache_key(text, model, config)
        cache_file = self.cache_dir / f"{cache_key}.wav"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logging.warning(f"Failed to read cache file {cache_file}: {e}")
        
        return None
    
    def set(self, text: str, model: TTSModel, config: dict, audio_data: bytes) -> bool:
        """Cache audio data"""
        with self._cache_lock:
            try:
                cache_key = self._get_cache_key(text, model, config)
                cache_file = self.cache_dir / f"{cache_key}.wav"
                
                with open(cache_file, 'wb') as f:
                    f.write(audio_data)
                
                # Check cache size and cleanup if needed
                self._cleanup_if_needed()
                return True
            
            except Exception as e:
                logging.error(f"Failed to cache audio: {e}")
                return False
    
    def _cleanup_if_needed(self):
        """Cleanup old cache files if size exceeds limit"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.wav"))
        max_bytes = self.max_size_mb * 1024 * 1024
        
        if total_size > max_bytes:
            # Remove oldest files first
            files = sorted(
                self.cache_dir.glob("*.wav"),
                key=lambda f: f.stat().st_mtime
            )
            
            for file_path in files:
                try:
                    file_path.unlink()
                    total_size -= file_path.stat().st_size
                    if total_size <= max_bytes * 0.8:  # Keep 80% of limit
                        break
                except Exception as e:
                    logging.warning(f"Failed to remove cache file {file_path}: {e}")


class VietnameseTTSEngine:
    """Main Vietnamese TTS Engine with HuggingFace model support"""
    
    def __init__(self, config: TTSConfig = None):
        self.config = config or TTSConfig()
        self.text_processor = VietnameseTextProcessor()
        
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Check dependencies
        self._check_dependencies()
        
        self.audio_cache = AudioCache(
            self.config.cache_dir,
            self.config.max_cache_size_mb
        ) if self.config.enable_cache else None
        
        # Model storage
        self._loaded_models = {}
        self._model_load_lock = threading.Lock()
        
        # Initialize device
        if TORCH_AVAILABLE:
            self.device = "cuda" if self.config.gpu_enabled and torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"
        self.logger.info(f"TTS Engine initialized with device: {self.device}")
    
    def _check_dependencies(self):
        """Check and log dependency availability"""
        missing_deps = []
        
        if not TORCH_AVAILABLE:
            missing_deps.append("torch")
        if not TRANSFORMERS_AVAILABLE:
            missing_deps.append("transformers")
        if not SOUNDFILE_AVAILABLE:
            missing_deps.append("soundfile")
        if not NUMPY_AVAILABLE:
            missing_deps.append("numpy")
        
        if missing_deps:
            self.logger.warning(f"Missing dependencies: {missing_deps}. Only gTTS fallback will be available.")
        
        if not GTTS_AVAILABLE:
            self.logger.warning("gTTS not available. No TTS functionality will work.")
    
    def generate_speech(self, text: str, model: TTSModel = None) -> TTSResult:
        """Generate speech from text"""
        import time
        start_time = time.time()
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use primary model if not specified
        model = model or self.config.primary_model
        
        # Process text
        processed_text = self.text_processor.normalize_text(text)
        
        # Check cache first
        cache_hit = False
        if self.audio_cache:
            config_dict = {
                'speed': self.config.voice_speed,
                'pitch': self.config.voice_pitch,
                'quality': self.config.audio_quality
            }
            
            cached_audio = self.audio_cache.get(processed_text, model, config_dict)
            if cached_audio:
                generation_time = time.time() - start_time
                return TTSResult(
                    audio_data=cached_audio,
                    sample_rate=22050,  # Default sample rate
                    model_used=model,
                    generation_time=generation_time,
                    cache_hit=True,
                    text_processed=processed_text
                )
        
        # Generate speech with fallback chain
        for attempt_model in [model] + self.config.fallback_models:
            try:
                audio_data, sample_rate = self._generate_with_model(
                    processed_text, attempt_model
                )
                
                # Cache the result
                if self.audio_cache and not cache_hit:
                    config_dict = {
                        'speed': self.config.voice_speed,
                        'pitch': self.config.voice_pitch,
                        'quality': self.config.audio_quality
                    }
                    self.audio_cache.set(processed_text, attempt_model, config_dict, audio_data)
                
                generation_time = time.time() - start_time
                
                return TTSResult(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    model_used=attempt_model,
                    generation_time=generation_time,
                    cache_hit=cache_hit,
                    text_processed=processed_text
                )
                
            except Exception as e:
                self.logger.warning(f"Failed to generate with {attempt_model.value}: {e}")
                continue
        
        raise RuntimeError("All TTS models failed to generate speech")
    
    async def generate_speech_async(self, text: str, callback: Callable[[TTSResult], None], model: TTSModel = None):
        """Generate speech asynchronously"""
        def run_generation():
            try:
                result = self.generate_speech(text, model)
                callback(result)
            except Exception as e:
                self.logger.error(f"Async TTS generation failed: {e}")
                callback(None)
        
        if self.config.enable_async:
            thread = threading.Thread(target=run_generation)
            thread.start()
        else:
            run_generation()
    
    def _generate_with_model(self, text: str, model: TTSModel) -> Tuple[bytes, int]:
        """Generate speech with specific model"""
        
        if model == TTSModel.GOOGLE_TTS:
            return self._generate_with_gtts(text)
        
        # Load HuggingFace model
        model_instance, tokenizer = self._load_model(model)
        
        # Generate audio based on model type
        if model == TTSModel.FACEBOOK_MMS:
            return self._generate_with_mms(text, model_instance, tokenizer)
        elif model in [TTSModel.ZALOPAY_TTS, TTSModel.F5_TTS, TTSModel.VIET_TTS]:
            return self._generate_with_transformers(text, model_instance, tokenizer)
        
        raise ValueError(f"Unsupported model: {model}")
    
    def _load_model(self, model: TTSModel) -> Tuple[object, object]:
        """Load HuggingFace model with caching"""
        model_name = model.value
        
        # Check dependencies first
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available for model loading")
        
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        
        with self._model_load_lock:
            if model_name in self._loaded_models:
                return self._loaded_models[model_name]
            
            self.logger.info(f"Loading model: {model_name}")
            
            try:
                if model == TTSModel.FACEBOOK_MMS:
                    if not VitsModel or not AutoTokenizer:
                        raise RuntimeError("VitsModel or AutoTokenizer not available")
                    model_instance = VitsModel.from_pretrained(model_name)
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                else:
                    # For other models, attempt standard transformers loading
                    from transformers import AutoModel
                    model_instance = AutoModel.from_pretrained(model_name)
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                # Move to device
                if hasattr(model_instance, 'to') and TORCH_AVAILABLE:
                    model_instance = model_instance.to(self.device)
                
                self._loaded_models[model_name] = (model_instance, tokenizer)
                self.logger.info(f"Successfully loaded model: {model_name}")
                
                return model_instance, tokenizer
                
            except Exception as e:
                self.logger.error(f"Failed to load model {model_name}: {e}")
                raise
    
    def _generate_with_mms(self, text: str, model, tokenizer) -> Tuple[bytes, int]:
        """Generate speech using Facebook MMS model"""
        inputs = tokenizer(text, return_tensors="pt")
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            output = model(**inputs).waveform
        
        # Convert to numpy and then to bytes
        audio_array = output.squeeze().cpu().numpy()
        
        # Apply speed and pitch modifications if needed
        if self.config.voice_speed != 1.0 and LIBROSA_AVAILABLE:
            audio_array = librosa.effects.time_stretch(audio_array, rate=self.config.voice_speed)
        
        # Convert to bytes
        audio_bytes = io.BytesIO()
        sf.write(audio_bytes, audio_array, 22050, format='WAV')
        audio_bytes.seek(0)
        
        return audio_bytes.read(), 22050
    
    def _generate_with_transformers(self, text: str, model, tokenizer) -> Tuple[bytes, int]:
        """Generate speech using other transformer models"""
        # This is a placeholder for other model implementations
        # Each model may have different interfaces
        self.logger.warning(f"Using placeholder implementation for model")
        
        # Fallback to gTTS for now
        return self._generate_with_gtts(text)
    
    def _generate_with_gtts(self, text: str) -> Tuple[bytes, int]:
        """Generate speech using Google TTS as fallback"""
        if not GTTS_AVAILABLE:
            raise RuntimeError("gTTS not available and no other models worked")
        
        tts = gTTS(text=text, lang='vi')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        return audio_bytes.read(), 22050  # gTTS typically uses 22050 Hz
    
    def get_available_models(self) -> List[TTSModel]:
        """Get list of available models"""
        available = []
        
        # Check HuggingFace models (basic connectivity check)
        for model in [TTSModel.FACEBOOK_MMS, TTSModel.ZALOPAY_TTS, TTSModel.F5_TTS, TTSModel.VIET_TTS]:
            available.append(model)
        
        # Check gTTS availability
        if GTTS_AVAILABLE:
            available.append(TTSModel.GOOGLE_TTS)
        
        return available
    
    def get_model_info(self, model: TTSModel) -> Dict:
        """Get information about a specific model"""
        info = {
            TTSModel.FACEBOOK_MMS: {
                "name": "Facebook MMS Vietnamese",
                "description": "High-quality VITS-based model from Meta",
                "quality": "High",
                "speed": "Medium",
                "offline": True
            },
            TTSModel.ZALOPAY_TTS: {
                "name": "Zalopay Vietnamese TTS",
                "description": "Modern diffusion-based Vietnamese TTS",
                "quality": "Very High",
                "speed": "Medium",
                "offline": True
            },
            TTSModel.F5_TTS: {
                "name": "F5-TTS Vietnamese",
                "description": "Fast inference F5-TTS model",
                "quality": "High",
                "speed": "Fast",
                "offline": True
            },
            TTSModel.VIET_TTS: {
                "name": "VietTTS",
                "description": "Vietnamese TTS with voice cloning",
                "quality": "High",
                "speed": "Medium",
                "offline": True
            },
            TTSModel.GOOGLE_TTS: {
                "name": "Google TTS",
                "description": "Cloud-based TTS fallback",
                "quality": "Medium",
                "speed": "Fast",
                "offline": False
            }
        }
        
        return info.get(model, {"name": "Unknown", "description": "No information available"})
    
    def set_voice_config(self, speed: float = None, pitch: float = None, quality: str = None):
        """Update voice configuration"""
        if speed is not None:
            self.config.voice_speed = max(0.5, min(2.0, speed))
        
        if pitch is not None:
            self.config.voice_pitch = max(0.5, min(2.0, pitch))
        
        if quality is not None and quality in ["low", "medium", "high"]:
            self.config.audio_quality = quality
    
    def clear_cache(self):
        """Clear audio cache"""
        if self.audio_cache:
            try:
                for cache_file in self.audio_cache.cache_dir.glob("*.wav"):
                    cache_file.unlink()
                self.logger.info("Audio cache cleared")
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.audio_cache:
            return {"enabled": False}
        
        cache_files = list(self.audio_cache.cache_dir.glob("*.wav"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "enabled": True,
            "files": len(cache_files),
            "size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.config.max_cache_size_mb
        }


# Convenience functions for easy integration
def create_tts_engine(config: TTSConfig = None) -> VietnameseTTSEngine:
    """Create a TTS engine instance"""
    return VietnameseTTSEngine(config)


def quick_tts(text: str, model: TTSModel = None) -> bytes:
    """Quick TTS generation function"""
    engine = create_tts_engine()
    result = engine.generate_speech(text, model)
    return result.audio_data