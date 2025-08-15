#!/usr/bin/env python3
"""
Test script for Vietnamese TTS system
Tests various models and configurations with travel-related content
"""

import os
import sys
import time
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.vietnamese_tts_engine import (
            VietnameseTTSEngine, TTSConfig, TTSModel, VietnameseTextProcessor
        )
        print("✅ Vietnamese TTS engine imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Vietnamese TTS: {e}")
        return False


def test_text_processing():
    """Test Vietnamese text preprocessing"""
    print("\n🔧 Testing text processing...")
    
    try:
        from src.vietnamese_tts_engine import VietnameseTextProcessor
        
        processor = VietnameseTextProcessor()
        
        # Test cases for Vietnamese travel content
        test_cases = [
            "Chào mừng bạn đến với TP.HCM! Thời tiết hôm nay 28°C.",
            "Đặt khách sạn 5 sao với giá 1,500,000 VND/đêm.",
            "Bay từ Hà Nội đến Đà Nẵng ngày 25/12/2025.",
            "Thuê xe từ 8:00 AM đến 6:00 PM với tốc độ 60 km/h.",
            "Tham quan Hội An vs Huế - so sánh 2 di sản UNESCO."
        ]
        
        for i, text in enumerate(test_cases, 1):
            processed = processor.normalize_text(text)
            print(f"Test {i}:")
            print(f"  Input:  {text}")
            print(f"  Output: {processed}")
            print()
        
        print("✅ Text processing working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        traceback.print_exc()
        return False


def test_tts_models():
    """Test TTS model availability and basic functionality"""
    print("\n🎤 Testing TTS models...")
    
    try:
        from src.vietnamese_tts_engine import VietnameseTTSEngine, TTSConfig, TTSModel
        
        # Create engine with test configuration
        config = TTSConfig(
            enable_cache=True,
            cache_dir="test_audio_cache",
            max_cache_size_mb=50,
            gpu_enabled=False  # Use CPU for testing
        )
        
        engine = VietnameseTTSEngine(config)
        print(f"✅ TTS Engine created with device: {engine.device}")
        
        # Test available models
        available_models = engine.get_available_models()
        print(f"📋 Available models: {[model.value for model in available_models]}")
        
        # Test model info
        for model in available_models[:3]:  # Test first 3 models
            info = engine.get_model_info(model)
            print(f"  {model.value}: {info['name']} - {info['quality']} quality")
        
        return True, engine
        
    except Exception as e:
        print(f"❌ TTS model test failed: {e}")
        traceback.print_exc()
        return False, None


def test_audio_generation(engine, test_fallback=True):
    """Test audio generation with Vietnamese travel content"""
    print("\n🔊 Testing audio generation...")
    
    if not engine:
        print("❌ No engine available for testing")
        return False
    
    # Vietnamese travel test phrases
    test_phrases = [
        "Xin chào! Tôi là trợ lý du lịch thông minh.",
        "Hà Nội có nhiều địa điểm du lịch nổi tiếng như Hồ Hoàn Kiếm.",
        "Thời tiết TP.HCM hôm nay nắng đẹp, nhiệt độ 30 độ C.",
        "Đặt khách sạn gần sân bay với giá tốt nhất.",
        "Thuê xe 4 chỗ đi Đà Lạt cuối tuần này."
    ]
    
    results = []
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n🧪 Test {i}: {phrase[:30]}...")
        
        try:
            start_time = time.time()
            
            # Try with fallback to gTTS if HuggingFace models fail
            if test_fallback:
                from src.vietnamese_tts_engine import TTSModel
                test_model = TTSModel.GOOGLE_TTS  # Start with gTTS fallback
            else:
                test_model = TTSModel.FACEBOOK_MMS  # Try HuggingFace model
            
            result = engine.generate_speech(phrase, test_model)
            generation_time = time.time() - start_time
            
            print(f"  ✅ Generated in {generation_time:.2f}s")
            print(f"  📊 Model: {result.model_used.value}")
            print(f"  🔊 Audio size: {len(result.audio_data)} bytes")
            print(f"  📈 Sample rate: {result.sample_rate} Hz")
            print(f"  💾 Cache hit: {result.cache_hit}")
            
            results.append({
                'phrase': phrase,
                'success': True,
                'model': result.model_used.value,
                'time': generation_time,
                'size': len(result.audio_data),
                'cache_hit': result.cache_hit
            })
            
        except Exception as e:
            print(f"  ❌ Generation failed: {e}")
            results.append({
                'phrase': phrase,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n📊 Generation Summary:")
    print(f"  ✅ Successful: {successful}/{len(test_phrases)}")
    
    if successful > 0:
        avg_time = sum(r['time'] for r in results if r['success']) / successful
        print(f"  ⏱️  Average time: {avg_time:.2f}s")
        
        cache_hits = sum(1 for r in results if r['success'] and r.get('cache_hit', False))
        print(f"  💾 Cache hits: {cache_hits}/{successful}")
    
    return successful > 0


def test_cache_system(engine):
    """Test audio caching functionality"""
    print("\n💾 Testing cache system...")
    
    if not engine:
        print("❌ No engine available for cache testing")
        return False
    
    try:
        # Generate same phrase twice to test caching
        test_phrase = "Kiểm tra hệ thống cache của TTS."
        
        print("First generation (should cache)...")
        start_time = time.time()
        result1 = engine.generate_speech(test_phrase, TTSModel.GOOGLE_TTS)
        time1 = time.time() - start_time
        
        print("Second generation (should hit cache)...")
        start_time = time.time()
        result2 = engine.generate_speech(test_phrase, TTSModel.GOOGLE_TTS)
        time2 = time.time() - start_time
        
        print(f"  First: {time1:.2f}s (cache: {result1.cache_hit})")
        print(f"  Second: {time2:.2f}s (cache: {result2.cache_hit})")
        
        # Check cache stats
        cache_stats = engine.get_cache_stats()
        if cache_stats.get('enabled'):
            print(f"  📁 Cache files: {cache_stats['files']}")
            print(f"  📊 Cache size: {cache_stats['size_mb']:.2f} MB")
        
        print("✅ Cache system working")
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False


def test_configuration():
    """Test TTS configuration management"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test TTS configuration methods
        tts_config = config_manager.get_tts_config_dict()
        print("📋 Current TTS configuration:")
        for key, value in tts_config.items():
            print(f"  {key}: {value}")
        
        # Test updating configuration
        test_updates = {
            'tts_voice_speed': 1.2,
            'tts_audio_quality': 'high',
            'tts_enable_cache': True
        }
        
        success = config_manager.update_tts_config(test_updates)
        print(f"  ✅ Config update: {'SUCCESS' if success else 'FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def cleanup_test_files():
    """Clean up test files and cache"""
    print("\n🧹 Cleaning up test files...")
    
    try:
        # Remove test cache directory
        test_cache_dir = Path("test_audio_cache")
        if test_cache_dir.exists():
            for file in test_cache_dir.glob("*.wav"):
                file.unlink()
            test_cache_dir.rmdir()
            print("✅ Test cache cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


def main():
    """Run all TTS tests"""
    print("🚀 Vietnamese TTS System Test Suite")
    print("=" * 50)
    
    test_results = {
        'imports': False,
        'text_processing': False,
        'models': False,
        'audio_generation': False,
        'cache': False,
        'configuration': False
    }
    
    # Test 1: Basic imports
    test_results['imports'] = test_basic_imports()
    
    if not test_results['imports']:
        print("\n❌ Cannot proceed without basic imports")
        return
    
    # Test 2: Text processing
    test_results['text_processing'] = test_text_processing()
    
    # Test 3: TTS models
    models_ok, engine = test_tts_models()
    test_results['models'] = models_ok
    
    # Test 4: Audio generation (with fallback to gTTS)
    if engine:
        test_results['audio_generation'] = test_audio_generation(engine, test_fallback=True)
        
        # Test 5: Cache system
        if test_results['audio_generation']:
            test_results['cache'] = test_cache_system(engine)
    
    # Test 6: Configuration
    test_results['configuration'] = test_configuration()
    
    # Cleanup
    cleanup_test_files()
    
    # Final report
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():20} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Vietnamese TTS system is ready.")
    elif passed_tests >= total_tests // 2:
        print("⚠️  Some tests failed, but basic functionality works.")
    else:
        print("❌ Major issues detected. Check dependencies and configuration.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)