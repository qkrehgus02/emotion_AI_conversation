import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { Colors } from '../constants/colors';

const VoiceRecorder = ({ onRecordingComplete, isProcessing }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(false);

  const recordingRef = useRef(null);
  const timerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    requestPermissions();
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const requestPermissions = async () => {
    try {
      if (Platform.OS === 'web') {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        setPermissionGranted(true);

        mediaRecorderRef.current.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const audioUrl = URL.createObjectURL(audioBlob);
          const audioFile = new File([audioBlob], "recording.webm", { type: "audio/webm" });
          onRecordingComplete(audioFile);
          audioChunksRef.current = [];
        };
      } else {
        const { status } = await Audio.requestPermissionsAsync();
        setPermissionGranted(status === 'granted');
      }
    } catch (error) {
      console.error('Error requesting permissions:', error);
      console.warn('마이크 권한 거부됨. HTTP 환경에서는 마이크 사용이 제한됩니다.');
      console.warn('해결 방법:');
      console.warn('1. Chrome 브라우저에서 chrome://flags/#unsafely-treat-insecure-origin-as-secure 접속');
      console.warn('2. http://172.16.10.36:3000 추가');
      console.warn('3. 또는 텍스트 입력 모드 사용');
      setPermissionGranted(false);
      // alert 제거하여 앱이 계속 실행되도록 함
    }
  };

  const startRecording = async () => {
    try {
      if (!permissionGranted) {
        await requestPermissions();
        return;
      }

      if (Platform.OS === 'web') {
        audioChunksRef.current = [];
        mediaRecorderRef.current.start();
      } else {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
        });

        const { recording } = await Audio.Recording.createAsync(
          Audio.RecordingOptionsPresets.HIGH_QUALITY
        );
        recordingRef.current = recording;
      }

      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('녹음을 시작할 수 없습니다. 마이크 권한을 확인해주세요.');
    }
  };

  const stopRecording = async () => {
    try {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setIsRecording(false);
      setIsPaused(false);

      if (Platform.OS === 'web') {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      } else {
        if (!recordingRef.current) return;
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();
        recordingRef.current = null;

        if (uri) {
          const fileInfo = await FileSystem.getInfoAsync(uri);
          const audioData = {
            uri: uri,
            type: 'audio/m4a',
            name: 'recording.m4a',
            size: fileInfo.size,
          };
          onRecordingComplete(audioData);
        }
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const pauseRecording = async () => {
    try {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setIsPaused(true);

      if (Platform.OS === 'web') {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.pause();
        }
      } else {
        if (recordingRef.current) {
          await recordingRef.current.pauseAsync();
        }
      }
    } catch (error) {
      console.error('Failed to pause recording:', error);
    }
  };

  const resumeRecording = async () => {
    try {
      setIsPaused(false);
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      if (Platform.OS === 'web') {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
          mediaRecorderRef.current.resume();
        }
      } else {
        if (recordingRef.current) {
          await recordingRef.current.startAsync();
        }
      }
    } catch (error) {
      console.error('Failed to resume recording:', error);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!permissionGranted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>마이크 권한이 필요합니다</Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermissions}>
          <Text style={styles.permissionButtonText}>권한 요청</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!isRecording ? (
        <TouchableOpacity
          style={[styles.recordButton, isProcessing && styles.recordButtonDisabled]}
          onPress={startRecording}
          disabled={isProcessing}
        >
          <View style={styles.recordButtonCircle} />
          <Text style={styles.recordButtonText}>녹음 시작</Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.recordingControls}>
          <View style={styles.recordingIndicator}>
            <View style={styles.recordingDot} />
            <Text style={styles.recordingTime}>{formatTime(recordingTime)}</Text>
          </View>

          <View style={styles.controlButtons}>
            {!isPaused ? (
              <TouchableOpacity style={styles.controlButton} onPress={pauseRecording}>
                <View style={styles.pauseIcon}>
                  <View style={styles.pauseBar} />
                  <View style={styles.pauseBar} />
                </View>
                <Text style={styles.controlButtonText}>일시정지</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.controlButton} onPress={resumeRecording}>
                <View style={styles.playIcon} />
                <Text style={styles.controlButtonText}>재개</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[styles.controlButton, styles.stopButton]}
              onPress={stopRecording}
            >
              <View style={styles.stopIcon} />
              <Text style={[styles.controlButtonText, styles.stopButtonText]}>전송</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {isProcessing && (
        <View style={styles.processingIndicator}>
          <Text style={styles.processingText}>처리 중...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    alignItems: 'center',
  },
  permissionContainer: {
    padding: 20,
    alignItems: 'center',
  },
  permissionText: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  permissionButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  recordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  recordButtonDisabled: {
    opacity: 0.5,
  },
  recordButtonCircle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#fff',
    marginRight: 8,
  },
  recordButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  recordingControls: {
    width: '100%',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.recording,
    marginRight: 8,
  },
  recordingTime: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  controlButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.buttonSecondary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  stopButton: {
    backgroundColor: Colors.primary,
  },
  controlButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textPrimary,
    marginLeft: 6,
  },
  stopButtonText: {
    color: '#fff',
  },
  pauseIcon: {
    flexDirection: 'row',
    gap: 3,
  },
  pauseBar: {
    width: 3,
    height: 14,
    backgroundColor: Colors.textPrimary,
  },
  playIcon: {
    width: 0,
    height: 0,
    borderLeftWidth: 10,
    borderRightWidth: 0,
    borderTopWidth: 7,
    borderBottomWidth: 7,
    borderLeftColor: Colors.textPrimary,
    borderRightColor: 'transparent',
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
  },
  stopIcon: {
    width: 12,
    height: 12,
    backgroundColor: '#fff',
  },
  processingIndicator: {
    marginTop: 12,
  },
  processingText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
});

export default VoiceRecorder;
