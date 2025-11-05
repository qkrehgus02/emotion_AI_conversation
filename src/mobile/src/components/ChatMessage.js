import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Audio } from 'expo-av';
import { Colors } from '../constants/colors';
import { EMOTION_CONFIG } from '../constants/config';

const ChatMessage = ({ message, isUser }) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [sound, setSound] = useState(null);

  const playAudio = async () => {
    if (message.audioUrl && !isPlayingAudio) {
      try {
        setIsPlayingAudio(true);

        const { sound: audioSound } = await Audio.Sound.createAsync(
          { uri: message.audioUrl },
          { shouldPlay: true }
        );

        setSound(audioSound);

        audioSound.setOnPlaybackStatusUpdate((status) => {
          if (status.didJustFinish) {
            setIsPlayingAudio(false);
            audioSound.unloadAsync();
          }
        });
      } catch (error) {
        console.error('Error playing audio:', error);
        setIsPlayingAudio(false);
      }
    }
  };

  const getEmotionEmoji = (emotion) => {
    return EMOTION_CONFIG.EMOJI_MAP[emotion?.toLowerCase()] || '💭';
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      {!isUser && message.emotion && (
        <View style={styles.emotionBadge}>
          <Text style={styles.emotionEmoji}>{getEmotionEmoji(message.emotion)}</Text>
          <Text style={styles.emotionText}>{message.emotion}</Text>
          {message.emotionProbability && (
            <Text style={styles.emotionProb}>
              {(message.emotionProbability * 100).toFixed(1)}%
            </Text>
          )}
        </View>
      )}

      <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
          {message.text}
        </Text>

        {message.timestamp && (
          <Text style={styles.messageTime}>{formatTime(message.timestamp)}</Text>
        )}
      </View>

      {!isUser && message.audioUrl && (
        <TouchableOpacity
          style={[styles.audioButton, isPlayingAudio && styles.audioButtonPlaying]}
          onPress={playAudio}
          disabled={isPlayingAudio}
        >
          <View style={isPlayingAudio ? styles.pauseIcon : styles.playIcon} />
          <Text style={styles.audioButtonText}>
            {isPlayingAudio ? '재생 중...' : '음성 듣기'}
          </Text>
        </TouchableOpacity>
      )}

      {!isUser && message.emotionTop3 && message.emotionTop3.length > 0 && (
        <View style={styles.emotionDetails}>
          <Text style={styles.detailsLabel}>감정 분석:</Text>
          {message.emotionTop3.map((emotion, idx) => (
            <View key={idx} style={styles.emotionItem}>
              <Text style={styles.emotionName}>{emotion.label}</Text>
              <View style={styles.emotionBarContainer}>
                <View
                  style={[
                    styles.emotionBarFill,
                    { width: `${emotion.probability * 100}%` },
                  ]}
                />
              </View>
              <Text style={styles.emotionPercentage}>
                {(emotion.probability * 100).toFixed(1)}%
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  emotionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.emotionBadge,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginBottom: 6,
  },
  emotionEmoji: {
    fontSize: 16,
    marginRight: 6,
  },
  emotionText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.emotionText,
    marginRight: 6,
  },
  emotionProb: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: Colors.userMessage,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: Colors.assistantMessage,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 20,
  },
  userText: {
    color: Colors.userMessageText,
  },
  assistantText: {
    color: Colors.assistantMessageText,
  },
  messageTime: {
    fontSize: 11,
    color: Colors.textLight,
    marginTop: 4,
  },
  audioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.buttonSecondary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginTop: 6,
  },
  audioButtonPlaying: {
    backgroundColor: Colors.primaryLight,
  },
  audioButtonText: {
    fontSize: 12,
    color: Colors.textPrimary,
    marginLeft: 6,
  },
  playIcon: {
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 0,
    borderTopWidth: 6,
    borderBottomWidth: 6,
    borderLeftColor: Colors.textPrimary,
    borderRightColor: 'transparent',
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
  },
  pauseIcon: {
    width: 12,
    height: 12,
    backgroundColor: Colors.textPrimary,
  },
  emotionDetails: {
    marginTop: 8,
    padding: 12,
    backgroundColor: Colors.cardBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '80%',
  },
  detailsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  emotionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  emotionName: {
    fontSize: 12,
    color: Colors.textPrimary,
    width: 60,
  },
  emotionBarContainer: {
    flex: 1,
    height: 6,
    backgroundColor: Colors.borderLight,
    borderRadius: 3,
    marginHorizontal: 8,
    overflow: 'hidden',
  },
  emotionBarFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 3,
  },
  emotionPercentage: {
    fontSize: 11,
    color: Colors.textSecondary,
    width: 45,
    textAlign: 'right',
  },
});

export default ChatMessage;
