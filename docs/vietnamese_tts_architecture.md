# Vietnamese Text-to-Speech Architecture Design

## Overview
This document outlines the architecture for implementing Vietnamese Text-to-Speech (TTS) functionality using state-of-the-art HuggingFace models to enhance the travel assistant's accessibility and user experience.

## Goals
- Provide high-quality Vietnamese speech synthesis
- Support multiple TTS models for fallback and quality options
- Enable real-time audio generation for chat responses
- Optimize performance with caching and async processing
- Maintain compatibility with existing gTTS implementation

## Selected Models

### Primary Models
1. **Facebook MMS-TTS Vietnamese** (`facebook/mms-tts-vie`)
   - Based on VITS architecture
   - Mature and well-tested
   - Part of Facebook's Massively Multilingual Speech project
   - Good balance of quality and performance

2. **Zalopay Vietnamese TTS** (`zalopay/vietnamese-tts`)
   - Modern architecture with diffusion transformer
   - Trained on 200+ hours of Vietnamese speech
   - High quality natural-sounding output
   - Actively maintained for 2025

3. **F5-TTS Vietnamese** (`hynt/F5-TTS-Vietnamese-100h`)
   - Based on F5-TTS architecture with ConvNeXt V2
   - Fast training and inference
   - Trained on diverse Vietnamese datasets (VLSP, VietTTS, YouTube)

### Fallback Options
- **Google TTS (gTTS)** - Current implementation as fallback
- **VietTTS** (`dangvansam/viet-tts`) - Voice cloning capabilities

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vietnamese TTS System                       │
├─────────────────────────────────────────────────────────────────┤
│  TTS Service Manager                                            │
│  ├── Model Registry (Facebook MMS, Zalopay, F5-TTS)           │
│  ├── Model Loader & Cache                                      │
│  ├── Text Preprocessing (Vietnamese normalization)             │
│  ├── Audio Generation Pipeline                                 │
│  └── Fallback Handler (gTTS)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Configuration Management                                       │
│  ├── Model Selection (Primary/Fallback)                       │
│  ├── Voice Settings (Speed, Pitch, Quality)                   │
│  ├── Performance Settings (Cache, Async)                      │
│  └── User Preferences                                          │
├─────────────────────────────────────────────────────────────────┤
│  Audio Cache System                                            │
│  ├── Hash-based Text Caching                                  │
│  ├── File Storage Management                                   │
│  ├── Cache Cleanup & Optimization                             │
│  └── Streaming Support                                         │
├─────────────────────────────────────────────────────────────────┤
│  UI Components                                                 │
│  ├── Enhanced Audio Player                                     │
│  ├── Voice Selection Controls                                  │
│  ├── Speed/Quality Controls                                    │
│  └── Download Audio Options                                    │
├─────────────────────────────────────────────────────────────────┤
│  Integration Layer                                             │
│  ├── Chat Message TTS                                         │
│  ├── Travel Content TTS                                       │
│  ├── Batch Processing                                         │
│  └── Real-time Generation                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core TTS Engine
- Create `VietnameTTSEngine` class with model management
- Implement model loading and caching
- Add Vietnamese text preprocessing
- Basic audio generation with primary models

### Phase 2: Configuration & Management
- Extend ConfigManager with TTS settings
- Add model selection and voice configuration
- Implement performance optimization settings
- User preference management

### Phase 3: Audio System Enhancement
- Audio caching with hash-based storage
- Streaming audio generation
- Batch processing for multiple texts
- Memory optimization

### Phase 4: UI/UX Integration
- Enhanced audio player components
- Voice selection interface
- Real-time generation indicators
- Download and sharing options

### Phase 5: Travel Assistant Integration
- Seamless chat message TTS
- Travel information narration
- Multi-language support prep
- Accessibility features

## Technical Specifications

### Model Requirements
```python
# Required packages
transformers>=4.33.0
torch>=1.11.0
soundfile>=0.12.0
librosa>=0.9.0
numpy>=1.21.0
scipy>=1.7.0
```

### API Interface
```python
class VietnameseTTSEngine:
    def __init__(self, config_manager: ConfigManager)
    def generate_speech(self, text: str, model: str = None) -> bytes
    def generate_speech_async(self, text: str, callback: callable)
    def set_voice_config(self, speed: float, pitch: float)
    def get_available_models(self) -> List[str]
    def get_model_info(self, model: str) -> Dict
```

### Cache Strategy
- Text hash as cache key (MD5 of normalized text)
- Audio files stored in `audio_cache/` directory
- LRU cache with configurable size limits
- Cleanup based on last access time

### Performance Targets
- Initial model load: < 10 seconds
- Audio generation: < 3 seconds for 100 words
- Cache hit rate: > 80% for repeated content
- Memory usage: < 2GB for loaded models

## Vietnamese Text Processing

### Normalization Pipeline
1. **Number conversion**: "123" → "một trăm hai mươi ba"
2. **Date/Time formatting**: "25/12/2025" → "ngày hai mươi lăm tháng mười hai năm hai nghìn không trăm hai mươi lăm"
3. **Currency formatting**: "100,000 VND" → "một trăm nghìn đồng"
4. **Abbreviation expansion**: "TP.HCM" → "Thành phố Hồ Chí Minh"
5. **Special characters handling**: Remove or replace non-speech characters

### Travel Domain Optimization
- Location name pronunciation improvements
- Travel terminology standardization
- Cultural context handling
- Regional dialect considerations

## Error Handling & Fallbacks

### Fallback Chain
1. Primary HuggingFace model (Facebook MMS)
2. Secondary HuggingFace model (Zalopay)
3. Tertiary HuggingFace model (F5-TTS)
4. Google TTS (gTTS) - current implementation
5. Error message with text display

### Error Recovery
- Model loading failures
- GPU/CPU resource limitations
- Network connectivity issues
- Text processing errors
- Audio generation failures

## Security & Privacy

### Data Handling
- No text storage beyond caching period
- Local audio generation preferred
- User consent for cloud-based fallbacks
- Secure cache file permissions

### Privacy Protection
- Optional cloud service usage
- Local model preference
- Data retention policies
- User control over audio generation

## Monitoring & Analytics

### Performance Metrics
- Model loading times
- Audio generation latency
- Cache hit/miss rates
- Error rates by model
- User preference trends

### Quality Metrics
- Audio quality scores
- User satisfaction ratings
- Text processing accuracy
- Model reliability stats

## Future Enhancements

### Advanced Features
- Voice cloning for personalized experience
- Emotion and tone control
- Multi-speaker support
- Real-time voice modification

### Integration Possibilities
- Voice commands (STT integration)
- Conversation mode
- Audio tour generation
- Multilingual support expansion

## Dependencies & Resources

### System Requirements
- Python 3.8+
- 4GB+ RAM for model loading
- GPU recommended for faster inference
- Storage for model cache (1-2GB)

### External Dependencies
- HuggingFace Hub access
- Optional: GPU compute capability
- Audio playback support
- File system write permissions

This architecture provides a robust foundation for implementing high-quality Vietnamese text-to-speech functionality while maintaining flexibility, performance, and user experience focus.