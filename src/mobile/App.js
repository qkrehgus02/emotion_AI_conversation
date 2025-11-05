import React, { useState, useRef, useEffect } from 'react';
import { View, TouchableOpacity, StyleSheet, Dimensions, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import Svg, { Path } from 'react-native-svg';

import EmotionCharacterPanel from './src/components/EmotionCharacterPanel';
import ChatScreen from './src/screens/ChatScreen';
import ConversationHistory from './src/components/ConversationHistory';
import { API_ENDPOINTS } from './src/constants/config';
import { Colors } from './src/constants/colors';

const { width } = Dimensions.get('window');

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [currentEmotion, setCurrentEmotion] = useState(null);
  const [activePanel, setActivePanel] = useState('emotion'); // 'emotion' or 'chat'
  const [lastUsedPanel, setLastUsedPanel] = useState('emotion'); // Track which panel was last used
  const [userTranscript, setUserTranscript] = useState('');
  const [llmResponse, setLlmResponse] = useState('');
  const [ttsAudioUrl, setTtsAudioUrl] = useState(null);
  const conversationHistoryRef = useRef(null);

  useEffect(() => {
    // Set up audio mode
    Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
    });

    startNewConversation();
  }, []);

  const startNewConversation = () => {
    const newId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setConversationId(newId);
    setMessages([]);
    setCurrentEmotion(null);
  };

  const loadConversation = async (convId) => {
    try {
      const response = await fetch(API_ENDPOINTS.HISTORY_CONVERSATION(convId));
      if (response.ok) {
        const data = await response.json();
        setConversationId(convId);

        // Convert messages to display format
        const displayMessages = data.messages.map((msg) => ({
          id: msg.id,
          text: msg.content,
          isUser: msg.role === 'user',
          emotion: msg.emotion,
          emotionProbability: msg.emotion_probability,
          timestamp: msg.created_at,
        }));

        setMessages(displayMessages);

        // Set last emotion from messages
        const lastUserMessage = displayMessages.reverse().find((m) => m.isUser && m.emotion);
        if (lastUserMessage) {
          setCurrentEmotion(lastUserMessage.emotion);
        }
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      alert('대화를 불러오는 중 오류가 발생했습니다.');
    }
  };

  const handleVoiceMessage = async (audioData) => {
    setIsProcessing(true);
    setLastUsedPanel('emotion'); // Voice messages are from emotion panel
    setUserTranscript('음성 메시지를 처리 중입니다...');
    setLlmResponse('');
    setTtsAudioUrl(null);

    try {
      // Add placeholder message
      const userMessage = {
        id: Date.now(),
        text: '음성 메시지를 처리 중입니다...',
        isUser: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Create FormData
      const formData = new FormData();

      if (audioData instanceof File) {
        // Web environment: audioData is a File object
        formData.append('audio', audioData, audioData.name);
      } else {
        // Native environment: audioData is an object with uri, type, name
        formData.append('audio', {
          uri: audioData.uri,
          type: audioData.type,
          name: audioData.name,
        });
      }

      if (conversationId) {
        formData.append('conversation_id', conversationId);
      }

      console.log('Sending audio:', audioData.size, 'bytes, type:', audioData.type);

      // Send to backend
      const response = await fetch(API_ENDPOINTS.CHAT_VOICE, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser will set it automatically with boundary
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update user transcript and emotion
      setUserTranscript(data.transcribed_text);
      setCurrentEmotion(data.detected_emotion);

      // Update user message with transcription
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id
            ? {
                ...msg,
                text: data.transcribed_text,
                emotion: data.detected_emotion,
                emotionProbability: data.emotion_probability,
                emotionTop3: data.emotion_top3,
              }
            : msg
        )
      );

      // Request TTS for assistant response
      const ttsResponse = await fetch(API_ENDPOINTS.CHAT_TTS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: data.llm_response }),
      });

      let audioUrl = null;
      if (ttsResponse.ok) {
        const audioBlob = await ttsResponse.blob();

        if (Platform.OS === 'web') {
          // Web: Use Blob URL directly
          audioUrl = URL.createObjectURL(audioBlob);
        } else {
          // React Native: Convert blob to base64 and save to file system
          const reader = new FileReader();
          const base64Promise = new Promise((resolve) => {
            reader.onloadend = () => {
              const base64data = reader.result.split(',')[1];
              resolve(base64data);
            };
            reader.readAsDataURL(audioBlob);
          });

          const base64data = await base64Promise;
          const fileUri = `${FileSystem.documentDirectory}tts_${Date.now()}.wav`;
          await FileSystem.writeAsStringAsync(fileUri, base64data, {
            encoding: FileSystem.EncodingType.Base64,
          });
          audioUrl = fileUri;
        }
      }

      // Update LLM response and TTS audio URL
      setLlmResponse(data.llm_response);
      setTtsAudioUrl(audioUrl);

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        text: data.llm_response,
        isUser: false,
        audioUrl: audioUrl,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Refresh conversation history
      if (conversationHistoryRef.current?.loadConversations) {
        conversationHistoryRef.current.loadConversations();
      }
    } catch (error) {
      console.error('Error processing voice message:', error);

      const errorMessage = {
        id: Date.now() + 2,
        text: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        isUser: false,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTextMessage = async (textMessage) => {
    setIsProcessing(true);
    setLastUsedPanel('chat'); // Text messages are from chat panel

    try {
      // Add user message immediately
      const userMessage = {
        id: Date.now(),
        text: textMessage,
        isUser: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to backend (text endpoint - no emotion analysis)
      const response = await fetch(API_ENDPOINTS.CHAT_TEXT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: textMessage,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Request TTS for assistant response
      const ttsResponse = await fetch(API_ENDPOINTS.CHAT_TTS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: data.response }),
      });

      let audioUrl = null;
      if (ttsResponse.ok) {
        const audioBlob = await ttsResponse.blob();

        if (Platform.OS === 'web') {
          // Web: Use Blob URL directly
          audioUrl = URL.createObjectURL(audioBlob);
        } else {
          // React Native: Convert blob to base64 and save to file system
          const reader = new FileReader();
          const base64Promise = new Promise((resolve) => {
            reader.onloadend = () => {
              const base64data = reader.result.split(',')[1];
              resolve(base64data);
            };
            reader.readAsDataURL(audioBlob);
          });

          const base64data = await base64Promise;
          const fileUri = `${FileSystem.documentDirectory}tts_${Date.now()}.wav`;
          await FileSystem.writeAsStringAsync(fileUri, base64data, {
            encoding: FileSystem.EncodingType.Base64,
          });
          audioUrl = fileUri;
        }
      }

      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        text: data.response,
        isUser: false,
        audioUrl: audioUrl,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Refresh conversation history
      if (conversationHistoryRef.current?.loadConversations) {
        conversationHistoryRef.current.loadConversations();
      }
    } catch (error) {
      console.error('Error processing text message:', error);

      const errorMessage = {
        id: Date.now() + 2,
        text: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        isUser: false,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Arrow button component
  const ArrowButton = ({ direction, onPress }) => (
    <TouchableOpacity style={styles.arrowButton} onPress={onPress}>
      <Svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        {direction === 'right' ? (
          <Path
            d="M9 18l6-6-6-6"
            stroke={Colors.primary}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : (
          <Path
            d="M15 18l-6-6 6-6"
            stroke={Colors.primary}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
      </Svg>
    </TouchableOpacity>
  );

  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.panelContainer}>
          {/* Left Panel: Emotion Character */}
          <View
            style={[
              styles.panel,
              styles.leftPanel,
              activePanel === 'emotion' && styles.activePanel,
              activePanel === 'chat' && styles.hiddenPanel,
            ]}
          >
            <EmotionCharacterPanel
              onVoiceMessage={handleVoiceMessage}
              isProcessing={lastUsedPanel === 'emotion' ? isProcessing : false}
              currentEmotion={currentEmotion}
              userTranscript={lastUsedPanel === 'emotion' ? userTranscript : ''}
              llmResponse={lastUsedPanel === 'emotion' ? llmResponse : ''}
              audioUrl={lastUsedPanel === 'emotion' ? ttsAudioUrl : null}
              isActive={activePanel === 'emotion'}
            />

            {/* Switch to chat button */}
            <View style={styles.rightArrowContainer}>
              <ArrowButton direction="right" onPress={() => setActivePanel('chat')} />
            </View>
          </View>

          {/* Right Panel: Chat + History */}
          <View
            style={[
              styles.panel,
              styles.rightPanel,
              activePanel === 'chat' && styles.activePanel,
              activePanel === 'emotion' && styles.hiddenPanel,
            ]}
          >
            {/* Switch to emotion button */}
            <View style={styles.leftArrowContainer}>
              <ArrowButton direction="left" onPress={() => setActivePanel('emotion')} />
            </View>

            <View style={styles.chatContainer}>
              <ChatScreen
                messages={messages}
                onVoiceMessage={handleVoiceMessage}
                onTextMessage={handleTextMessage}
                isProcessing={isProcessing}
              />
            </View>

            {/* History section at bottom */}
            <View style={styles.historyContainer}>
              <ConversationHistory
                ref={conversationHistoryRef}
                currentConversationId={conversationId}
                onSelectConversation={loadConversation}
                onNewConversation={startNewConversation}
              />
            </View>
          </View>
        </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  panelContainer: {
    flex: 1,
    flexDirection: 'row',
  },
  panel: {
    flex: 1,
    position: 'relative',
  },
  leftPanel: {
    backgroundColor: Colors.primary,
  },
  rightPanel: {
    backgroundColor: Colors.background,
  },
  activePanel: {
    // Active panel styling
  },
  hiddenPanel: {
    display: width < 768 ? 'none' : 'flex', // Hide on mobile, show on tablet
  },
  arrowButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
  },
  rightArrowContainer: {
    position: 'absolute',
    right: -24,
    top: '50%',
    marginTop: -24,
    zIndex: 100,
  },
  leftArrowContainer: {
    position: 'absolute',
    left: -24,
    top: '50%',
    marginTop: -24,
    zIndex: 100,
  },
  chatContainer: {
    flex: 1,
  },
  historyContainer: {
    height: 200,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
});
