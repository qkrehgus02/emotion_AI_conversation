import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Image, ScrollView } from 'react-native';
import { Audio } from 'expo-av';
import VoiceRecorder from './VoiceRecorder';
import { Colors } from '../constants/colors';

const EmotionCharacterPanel = ({
  onVoiceMessage,
  isProcessing,
  currentEmotion,
  userTranscript,
  llmResponse,
  audioUrl,
  isActive = true
}) => {
  const soundRef = useRef(null);

  // Auto-play TTS audio when available (only when panel is active)
  useEffect(() => {
    const playAudio = async () => {
      if (audioUrl && !isProcessing && isActive) {
        try {
          // Unload previous sound if exists
          if (soundRef.current) {
            await soundRef.current.unloadAsync();
          }

          const { sound } = await Audio.Sound.createAsync(
            { uri: audioUrl },
            { shouldPlay: true }
          );

          soundRef.current = sound;

          sound.setOnPlaybackStatusUpdate((status) => {
            if (status.didJustFinish) {
              sound.unloadAsync();
              soundRef.current = null;
            }
          });
        } catch (error) {
          console.error('Error auto-playing TTS audio:', error);
        }
      }
    };

    playAudio();

    // Cleanup on unmount or when component becomes inactive
    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync();
        soundRef.current = null;
      }
    };
  }, [audioUrl, isProcessing, isActive]);
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>감정 인식 AI</Text>
        <Text style={styles.subtitle}>음성으로 대화하세요</Text>
      </View>

      <View style={styles.characterContainer}>
        {/* LLM Response - Above Duck */}
        {llmResponse && (
          <View style={styles.responseContainer}>
            <ScrollView
              style={styles.responseScroll}
              contentContainerStyle={styles.responseContent}
            >
              <Text style={styles.responseText}>{llmResponse}</Text>
            </ScrollView>
          </View>
        )}

        {/* Duck Character */}
        <View style={[styles.characterDisplay, isProcessing && styles.processing]}>
          <Image
            source={require('../../assets/duck-character.png')}
            style={styles.duckImage}
            resizeMode="contain"
          />

          {isProcessing && (
            <View style={styles.processingBadge}>
              <ActivityIndicator size="small" color="#fff" />
            </View>
          )}
        </View>

        {/* User Transcript - Below Duck */}
        {userTranscript && (
          <View style={styles.transcriptContainer}>
            <Text style={styles.transcriptLabel}>내 말:</Text>
            <Text style={styles.transcriptText}>{userTranscript}</Text>
          </View>
        )}
      </View>

      <View style={styles.voiceInputSection}>
        <VoiceRecorder onRecordingComplete={onVoiceMessage} isProcessing={isProcessing} />

        <View style={styles.voiceHint}>
          <Text style={styles.hintText}>🎤 버튼을 눌러 음성으로 대화를 시작하세요</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.cardBackground,
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  characterContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  characterDisplay: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  processing: {
    opacity: 0.8,
  },
  duckImage: {
    width: 300,
    height: 300,
  },
  processingBadge: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: Colors.primary,
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  responseContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    maxHeight: 150,
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  responseScroll: {
    maxHeight: 110,
  },
  responseContent: {
    alignItems: 'center',
  },
  responseText: {
    fontSize: 16,
    color: Colors.textPrimary,
    textAlign: 'center',
    lineHeight: 24,
  },
  transcriptContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 16,
    padding: 16,
    marginTop: 20,
    width: '100%',
    alignItems: 'center',
  },
  transcriptLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: 6,
    fontWeight: '600',
  },
  transcriptText: {
    fontSize: 15,
    color: Colors.textPrimary,
    textAlign: 'center',
    lineHeight: 22,
  },
  voiceInputSection: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  voiceHint: {
    marginTop: 16,
    alignItems: 'center',
  },
  hintText: {
    fontSize: 14,
    color: Colors.textPrimary,
    textAlign: 'center',
  },
});

export default EmotionCharacterPanel;
