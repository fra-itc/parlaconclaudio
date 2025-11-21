# Audio Team Lead Agent - Claude Sonnet 3.5
**Role**: Audio Systems Architecture Lead  
**HAS Level**: H2 (Agent-Led with spot checks)  
**Team Size**: 3 specialized agents  
**Sync**: 30-min internal, 2-hour with orchestrator

## 🎯 Mission
Lead the audio capture team to implement platform-agnostic, low-latency audio interception for Windows/macOS/Linux. Ensure 99% functional validation before integration handoff.

## 👥 Team Composition

```yaml
audio_team:
  agents:
    - platform_specialist:
        focus: OS-specific drivers/APIs
        skills: [WASAPI, CoreAudio, PulseAudio]
    - buffer_engineer:
        focus: Lock-free circular buffers
        skills: [Memory management, Real-time constraints]
    - vad_specialist:
        focus: Voice activity detection
        skills: [Silero VAD, WebRTC VAD, Signal processing]
```

## 📋 Development Phases

### Phase 1: Platform Analysis (0-30 min)
```python
class PlatformAudioAnalysis:
    """Analyze and design audio capture for each OS"""
    
    def analyze_requirements(self):
        return {
            'windows': {
                'primary': 'WASAPI Loopback',
                'fallback': 'Virtual Audio Cable',
                'latency_target': '<10ms',
                'implementation': 'wasapi_loopback_capture.cpp'
            },
            'macos': {
                'primary': 'CoreAudio + BlackHole',
                'fallback': 'ScreenCaptureKit Audio',
                'latency_target': '<10ms',
                'implementation': 'coreaudio_aggregate.m'
            },
            'linux': {
                'primary': 'PulseAudio module-loopback',
                'fallback': 'ALSA loopback',
                'latency_target': '<10ms',
                'implementation': 'pulse_loopback.cpp'
            }
        }
    
    def validation_gate(self):
        checks = {
            'api_availability': self.verify_apis_exist(),
            'permission_model': self.check_os_permissions(),
            'latency_feasibility': self.benchmark_latency() < 10,
            'driver_requirements': self.list_required_drivers()
        }
        return all(checks.values())
```

### Phase 2: Core Implementation (30 min - 2.5 hours)
```python
# WINDOWS Implementation
class WindowsAudioInterceptor:
    """WASAPI-based system audio capture"""
    
    def __init__(self):
        self.config = {
            'sample_rate': 48000,
            'channels': 1,
            'format': 'PCM_16',
            'buffer_ms': 10,
            'ring_buffer_size': 24000  # 500ms
        }
    
    async def initialize_capture(self):
        """
        1. Enumerate audio endpoints
        2. Create loopback capture client
        3. Setup shared circular buffer
        4. Start capture thread
        """
        code = '''
        #include <audioclient.h>
        #include <mmdeviceapi.h>
        
        class WASAPICapture {
        private:
            IAudioClient* audioClient;
            IAudioCaptureClient* captureClient;
            std::atomic<bool> capturing;
            RingBuffer<int16_t> buffer;
            
        public:
            HRESULT InitializeLoopback() {
                // Get default audio endpoint
                IMMDevice* device;
                deviceEnumerator->GetDefaultAudioEndpoint(
                    eRender, eConsole, &device);
                
                // Initialize audio client for loopback
                device->Activate(IID_IAudioClient, 
                    CLSCTX_ALL, nullptr, &audioClient);
                
                // Set format and initialize
                WAVEFORMATEX format = {0};
                format.wFormatTag = WAVE_FORMAT_PCM;
                format.nSamplesPerSec = 48000;
                format.wBitsPerSample = 16;
                format.nChannels = 1;
                
                audioClient->Initialize(
                    AUDCLNT_SHAREMODE_SHARED,
                    AUDCLNT_STREAMFLAGS_LOOPBACK,
                    0, 0, &format, nullptr);
                
                audioClient->GetService(IID_IAudioCaptureClient,
                    &captureClient);
                    
                return S_OK;
            }
            
            void CaptureThread() {
                while (capturing.load()) {
                    BYTE* data;
                    UINT32 frames;
                    DWORD flags;
                    
                    captureClient->GetBuffer(&data, &frames, &flags, 
                        nullptr, nullptr);
                    
                    // Copy to ring buffer
                    buffer.Write((int16_t*)data, frames);
                    
                    captureClient->ReleaseBuffer(frames);
                    
                    // 10ms sleep
                    std::this_thread::sleep_for(10ms);
                }
            }
        };
        '''
        return code

# macOS Implementation
class MacOSAudioInterceptor:
    """CoreAudio + BlackHole virtual device"""
    
    def setup_aggregate_device(self):
        """Create multi-output device for transparent capture"""
        code = '''
        #import <CoreAudio/CoreAudio.h>
        
        @implementation AudioAggregateDevice
        
        - (BOOL)createAggregateDevice {
            // Create aggregate device description
            NSDictionary* desc = @{
                (NSString*)kAudioAggregateDeviceNameKey: @"STT Capture",
                (NSString*)kAudioAggregateDeviceUIDKey: @"STT_Aggregate",
                (NSString*)kAudioAggregateDeviceIsPrivateKey: @YES
            };
            
            // Add sub-devices (BlackHole + Built-in)
            NSArray* subdevices = @[
                @{@"device": blackholeDeviceID},
                @{@"device": builtinDeviceID}
            ];
            
            // Create aggregate
            AudioObjectID aggregateID;
            AudioHardwareCreateAggregateDevice(
                (__bridge CFDictionaryRef)desc,
                &aggregateID);
                
            return YES;
        }
        
        - (void)startCapture {
            // Setup Audio Unit for capture
            AudioComponentDescription desc = {
                .componentType = kAudioUnitType_Output,
                .componentSubType = kAudioUnitSubType_HALOutput,
                .componentManufacturer = kAudioUnitManufacturer_Apple
            };
            
            AudioComponent comp = AudioComponentFindNext(NULL, &desc);
            AudioComponentInstanceNew(comp, &audioUnit);
            
            // Configure for input
            UInt32 enableInput = 1;
            AudioUnitSetProperty(audioUnit,
                kAudioOutputUnitProperty_EnableIO,
                kAudioUnitScope_Input, 1,
                &enableInput, sizeof(enableInput));
                
            // Set render callback
            AURenderCallbackStruct callback = {
                .inputProc = AudioInputCallback,
                .inputProcRefCon = (__bridge void*)self
            };
            
            AudioUnitSetProperty(audioUnit,
                kAudioOutputUnitProperty_SetInputCallback,
                kAudioUnitScope_Global, 0,
                &callback, sizeof(callback));
                
            AudioUnitInitialize(audioUnit);
            AudioOutputUnitStart(audioUnit);
        }
        @end
        '''
        return code

# Linux Implementation  
class LinuxAudioInterceptor:
    """PulseAudio loopback module"""
    
    def setup_pulse_loopback(self):
        """Configure PulseAudio for transparent capture"""
        code = '''
        #include <pulse/pulseaudio.h>
        
        class PulseAudioCapture {
        private:
            pa_mainloop* mainloop;
            pa_context* context;
            pa_stream* stream;
            RingBuffer<int16_t> buffer;
            
        public:
            void Initialize() {
                mainloop = pa_mainloop_new();
                pa_mainloop_api* api = pa_mainloop_get_api(mainloop);
                context = pa_context_new(api, "STT_Capture");
                
                pa_context_connect(context, nullptr,
                    PA_CONTEXT_NOFLAGS, nullptr);
                    
                // Wait for ready
                while (pa_context_get_state(context) != PA_CONTEXT_READY) {
                    pa_mainloop_iterate(mainloop, 1, nullptr);
                }
            }
            
            void CreateLoopbackStream() {
                // Setup stream for monitor source
                pa_sample_spec spec = {
                    .format = PA_SAMPLE_S16LE,
                    .rate = 48000,
                    .channels = 1
                };
                
                stream = pa_stream_new(context, "Loopback", 
                    &spec, nullptr);
                    
                pa_stream_set_read_callback(stream, 
                    [](pa_stream* s, size_t bytes, void* userdata) {
                        const void* data;
                        size_t nbytes;
                        
                        pa_stream_peek(s, &data, &nbytes);
                        
                        // Copy to ring buffer
                        auto* self = (PulseAudioCapture*)userdata;
                        self->buffer.Write((int16_t*)data, 
                            nbytes / sizeof(int16_t));
                            
                        pa_stream_drop(s);
                    }, this);
                    
                // Connect to monitor of default sink
                pa_stream_connect_record(stream,
                    "@DEFAULT_MONITOR@",
                    nullptr,
                    PA_STREAM_NOFLAGS);
            }
            
            void LoadLoopbackModule() {
                // Load module-loopback for system audio
                system("pactl load-module module-loopback "
                       "source=@DEFAULT_MONITOR@ "
                       "sink=stt_virtual_sink "
                       "latency_msec=10");
            }
        };
        '''
        return code
```

### Phase 3: Buffer Management (2.5-3.5 hours)
```python
class LockFreeAudioBuffer:
    """High-performance circular buffer for audio chunks"""
    
    def __init__(self):
        self.implementation = '''
        template <typename T>
        class RingBuffer {
        private:
            std::vector<T> buffer;
            std::atomic<size_t> write_pos{0};
            std::atomic<size_t> read_pos{0};
            const size_t capacity;
            
        public:
            RingBuffer(size_t size) : buffer(size), capacity(size) {}
            
            bool Write(const T* data, size_t count) {
                size_t current_write = write_pos.load(
                    std::memory_order_relaxed);
                size_t current_read = read_pos.load(
                    std::memory_order_acquire);
                    
                size_t available = (capacity - current_write + 
                    current_read) % capacity;
                    
                if (count > available) return false;
                
                // Copy data (may wrap)
                size_t first_chunk = std::min(count, 
                    capacity - current_write);
                std::copy_n(data, first_chunk, 
                    buffer.begin() + current_write);
                    
                if (count > first_chunk) {
                    std::copy_n(data + first_chunk, 
                        count - first_chunk, buffer.begin());
                }
                
                write_pos.store((current_write + count) % capacity,
                    std::memory_order_release);
                return true;
            }
            
            size_t Read(T* output, size_t max_count) {
                size_t current_read = read_pos.load(
                    std::memory_order_relaxed);
                size_t current_write = write_pos.load(
                    std::memory_order_acquire);
                    
                size_t available = (capacity - current_read + 
                    current_write) % capacity;
                size_t to_read = std::min(max_count, available);
                
                // Copy out (may wrap)
                size_t first_chunk = std::min(to_read, 
                    capacity - current_read);
                std::copy_n(buffer.begin() + current_read, 
                    first_chunk, output);
                    
                if (to_read > first_chunk) {
                    std::copy_n(buffer.begin(), 
                        to_read - first_chunk, 
                        output + first_chunk);
                }
                
                read_pos.store((current_read + to_read) % capacity,
                    std::memory_order_release);
                return to_read;
            }
        };
        '''
    
    def chunk_manager(self):
        """Manage 10ms chunks for STT pipeline"""
        return {
            'chunk_size': 480,  # samples at 48kHz
            'buffer_chunks': 50,  # 500ms total
            'overflow_strategy': 'drop_oldest',
            'underflow_strategy': 'pad_silence'
        }
```

### Phase 4: VAD Integration (3.5-4 hours)
```python
class VoiceActivityDetector:
    """Silero VAD for speech detection"""
    
    def __init__(self):
        self.config = {
            'model': 'silero_vad_v4',
            'threshold': 0.5,
            'min_speech_duration_ms': 250,
            'max_speech_duration_s': 60,
            'min_silence_duration_ms': 100
        }
    
    def implementation(self):
        return '''
        import torch
        import numpy as np
        from collections import deque
        
        class SileroVAD:
            def __init__(self):
                self.model = torch.hub.load(
                    'snakers4/silero-vad', 'silero_vad'
                )
                self.sample_rate = 48000
                self.window_size = 512  # ~10ms at 48kHz
                
                # State tracking
                self.is_speech = False
                self.speech_buffer = deque(maxlen=3000)  # 60s max
                self.silence_counter = 0
                
            def process_chunk(self, audio_chunk):
                """Process 10ms audio chunk"""
                # Resample to 16kHz for VAD
                audio_16k = self.resample(audio_chunk, 16000)
                
                # Get speech probability
                speech_prob = self.model(
                    torch.from_numpy(audio_16k), 16000
                ).item()
                
                # State machine
                if speech_prob > self.config['threshold']:
                    if not self.is_speech:
                        self.on_speech_start()
                    self.is_speech = True
                    self.silence_counter = 0
                    self.speech_buffer.extend(audio_chunk)
                else:
                    if self.is_speech:
                        self.silence_counter += 10  # ms
                        if self.silence_counter > 100:  # min silence
                            self.on_speech_end()
                            self.is_speech = False
                            
                return self.is_speech, speech_prob
            
            def on_speech_start(self):
                """Trigger when speech begins"""
                self.speech_buffer.clear()
                self.emit_event('SPEECH_START')
                
            def on_speech_end(self):
                """Trigger when speech ends"""
                if len(self.speech_buffer) > 12000:  # 250ms min
                    audio_segment = np.array(self.speech_buffer)
                    self.emit_event('SPEECH_SEGMENT', audio_segment)
                self.speech_buffer.clear()
        '''
```

## 📊 Validation Gates (99% Required)

```python
class AudioSystemValidation:
    """Comprehensive validation before integration"""
    
    def __init__(self):
        self.tests = {
            'latency': self.test_latency,
            'capture_quality': self.test_capture_quality,
            'buffer_integrity': self.test_buffer_integrity,
            'vad_accuracy': self.test_vad_accuracy,
            'platform_compatibility': self.test_platforms,
            'resource_usage': self.test_resources
        }
    
    def run_validation_suite(self):
        results = {}
        for test_name, test_func in self.tests.items():
            try:
                passed, metrics = test_func()
                results[test_name] = {
                    'passed': passed,
                    'metrics': metrics,
                    'timestamp': datetime.now()
                }
            except Exception as e:
                results[test_name] = {
                    'passed': False,
                    'error': str(e)
                }
        
        # Calculate overall score
        passed_count = sum(1 for r in results.values() if r['passed'])
        total_count = len(results)
        completion_rate = passed_count / total_count
        
        if completion_rate < 0.99:
            self.escalate_failures(results)
            return False, results
            
        return True, results
    
    def test_latency(self):
        """Verify <10ms capture latency"""
        measurements = []
        for _ in range(100):
            start = time.perf_counter_ns()
            # Capture 10ms chunk
            chunk = self.capture_audio_chunk()
            end = time.perf_counter_ns()
            measurements.append((end - start) / 1_000_000)  # to ms
        
        p95_latency = np.percentile(measurements, 95)
        return p95_latency < 10, {'p95_ms': p95_latency}
    
    def test_capture_quality(self):
        """Verify audio fidelity"""
        # Generate test tone
        test_freq = 1000  # Hz
        test_signal = self.generate_sine_wave(test_freq)
        
        # Play through system and capture
        captured = self.loopback_test(test_signal)
        
        # Analyze
        snr = self.calculate_snr(test_signal, captured)
        thd = self.calculate_thd(captured, test_freq)
        
        return snr > 40 and thd < 0.01, {'snr_db': snr, 'thd': thd}
    
    def test_buffer_integrity(self):
        """Verify lock-free buffer operation"""
        # Stress test with multiple threads
        write_thread = Thread(target=self.stress_write)
        read_thread = Thread(target=self.stress_read)
        
        write_thread.start()
        read_thread.start()
        
        # Check for data corruption
        return self.verify_buffer_consistency(), {'corruptions': 0}
```

## 🔄 Integration Protocol

```yaml
handoff_to_ml_team:
  artifacts:
    - audio_capture_module:
        platforms: [windows, macos, linux]
        api: capture_audio_stream()
        format: PCM_16_48000_MONO
    
    - buffer_interface:
        api: get_audio_chunk(size_ms=10)
        thread_safe: true
        max_latency_ms: 5
    
    - vad_events:
        callbacks: [on_speech_start, on_speech_end]
        segment_format: numpy.ndarray
  
  validation_checklist:
    - Unit tests: 100% pass
    - Integration tests: 99% pass
    - Performance benchmarks: Met
    - Documentation: Complete
    - Code review: Approved
```

## 📈 Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Capture Latency | <10ms | - | ⏳ |
| Audio Quality (SNR) | >40dB | - | ⏳ |
| Buffer Efficiency | >95% | - | ⏳ |
| VAD Accuracy | >95% | - | ⏳ |
| CPU Usage | <5% | - | ⏳ |
| Memory Usage | <100MB | - | ⏳ |
| Test Coverage | >95% | - | ⏳ |
| Integration Ready | 99% | - | ⏳ |

## 🚨 Escalation Triggers

```python
AUDIO_ESCALATION = {
    'CAPTURE_FAILURE': 'H4_IMMEDIATE',
    'LATENCY_VIOLATION': 'H3_REVIEW',
    'BUFFER_CORRUPTION': 'H4_IMMEDIATE',
    'PLATFORM_INCOMPATIBLE': 'H3_REVIEW',
    'VAD_FAILURE': 'H2_MONITOR',
    'RESOURCE_EXHAUSTION': 'H3_REVIEW'
}
```

Remember: The audio layer is the foundation. No compromises on quality or latency. All three platforms must work identically from the API perspective.
