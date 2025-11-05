import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../constants/colors';
import { API_ENDPOINTS } from '../constants/config';

const ConversationHistory = forwardRef(
  ({ currentConversationId, onSelectConversation, onNewConversation }, ref) => {
    const [conversations, setConversations] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
      loadConversations();
    }, []);

    const loadConversations = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${API_ENDPOINTS.HISTORY_CONVERSATIONS}?limit=50`);
        if (response.ok) {
          const data = await response.json();
          setConversations(data);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    useImperativeHandle(ref, () => ({
      loadConversations,
    }));

    const deleteConversation = async (conversationId) => {
      console.log('Delete button clicked for conversation:', conversationId);

      const confirmed = window.confirm('이 대화를 삭제하시겠습니까?');
      if (!confirmed) {
        console.log('Delete cancelled');
        return;
      }

      console.log('Delete confirmed, calling API...');
      try {
        const url = API_ENDPOINTS.HISTORY_CONVERSATION(conversationId);
        console.log('DELETE URL:', url);

        const response = await fetch(url, {
          method: 'DELETE',
        });

        console.log('Delete response status:', response.status);

        if (response.ok) {
          console.log('Delete successful, updating UI...');
          setConversations(conversations.filter((c) => c.id !== conversationId));

          if (conversationId === currentConversationId) {
            onNewConversation();
          }
        } else {
          const errorText = await response.text();
          console.error('Delete failed:', response.status, errorText);
          alert('대화 삭제에 실패했습니다.');
        }
      } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('대화 삭제 중 오류가 발생했습니다: ' + error.message);
      }
    };

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return '방금 전';
      if (diffMins < 60) return `${diffMins}분 전`;
      if (diffHours < 24) return `${diffHours}시간 전`;
      if (diffDays < 7) return `${diffDays}일 전`;

      return date.toLocaleDateString('ko-KR', {
        month: 'short',
        day: 'numeric',
      });
    };

    const renderConversationItem = ({ item }) => (
      <View
        style={[
          styles.conversationItem,
          item.id === currentConversationId && styles.activeConversation,
        ]}
      >
        <TouchableOpacity
          style={styles.conversationTouchable}
          onPress={() => onSelectConversation(item.id)}
        >
          <View style={styles.conversationInfo}>
            <Text style={styles.conversationTitle} numberOfLines={1}>
              {item.title || '새 대화'}
            </Text>
            <Text style={styles.conversationPreview} numberOfLines={2}>
              {item.last_message || '메시지 없음'}
            </Text>
            <View style={styles.conversationMeta}>
              <Text style={styles.messageCount}>💬 {item.message_count}</Text>
              <Text style={styles.conversationDate}>{formatDate(item.updated_at)}</Text>
            </View>
          </View>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => deleteConversation(item.id)}
        >
          <Text style={styles.deleteButtonText}>×</Text>
        </TouchableOpacity>
      </View>
    );

    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>대화 기록</Text>
          <TouchableOpacity style={styles.newChatButton} onPress={onNewConversation}>
            <Text style={styles.newChatButtonText}>+</Text>
          </TouchableOpacity>
        </View>

        {isLoading ? (
          <View style={styles.loadingState}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>로딩 중...</Text>
          </View>
        ) : conversations.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>아직 대화 기록이 없습니다</Text>
            <Text style={styles.emptyHint}>새 대화를 시작해보세요</Text>
          </View>
        ) : (
          <FlatList
            data={conversations}
            renderItem={renderConversationItem}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContainer}
          />
        )}
      </View>
    );
  }
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.cardBackground,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  newChatButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  newChatButtonText: {
    fontSize: 24,
    color: '#fff',
    fontWeight: '600',
  },
  loadingState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: Colors.textSecondary,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  emptyHint: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  listContainer: {
    padding: 12,
  },
  conversationItem: {
    flexDirection: 'row',
    backgroundColor: Colors.background,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  activeConversation: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primaryLight + '15',
  },
  conversationTouchable: {
    flex: 1,
    padding: 16,
  },
  conversationInfo: {
    flex: 1,
  },
  conversationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 6,
  },
  conversationPreview: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  conversationMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  messageCount: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  conversationDate: {
    fontSize: 12,
    color: Colors.textLight,
  },
  deleteButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  deleteButtonText: {
    fontSize: 28,
    color: Colors.textLight,
    fontWeight: '300',
    lineHeight: 28,
  },
});

ConversationHistory.displayName = 'ConversationHistory';

export default ConversationHistory;
