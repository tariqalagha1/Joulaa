import React from 'react'
import { useTranslation } from 'react-i18next'
import { Bot, User, Copy, ThumbsUp, ThumbsDown, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Message } from '../../services/conversationService'
import toast from 'react-hot-toast'

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
  onRegenerate?: () => void
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isStreaming = false,
  onRegenerate,
  onFeedback
}) => {
  const { t } = useTranslation()
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      toast.success(t('chat.copied'))
    } catch (error) {
      toast.error(t('chat.copyError'))
    }
  }

  const handleFeedback = (feedback: 'positive' | 'negative') => {
    if (onFeedback) {
      onFeedback(message.id, feedback)
      toast.success(t('chat.feedbackSent'))
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-4 p-4 ${
        isUser ? 'bg-transparent' : 'bg-gray-50'
      }`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser 
          ? 'bg-primary-100 text-primary-600' 
          : 'bg-secondary-100 text-secondary-600'
      }`}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-sm text-gray-900">
            {isUser ? t('chat.you') : t('chat.assistant')}
          </span>
          <span className="text-xs text-gray-500">
            {new Date(message.created_at).toLocaleTimeString('ar-SA', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
          {message.tokens_used && (
            <span className="text-xs text-gray-400">
              {message.tokens_used} {t('chat.tokens')}
            </span>
          )}
        </div>

        {/* Message Text */}
        <div className={`prose prose-sm max-w-none ${
          isUser ? 'text-gray-900' : 'text-gray-800'
        }`}>
          {isAssistant ? (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={tomorrow}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* Streaming indicator */}
        {isStreaming && (
          <div className="flex items-center gap-2 mt-2">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-xs text-gray-500">{t('chat.thinking')}</span>
          </div>
        )}

        {/* Message Actions */}
        {!isStreaming && (
          <div className="flex items-center gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              title={t('chat.copy')}
            >
              <Copy size={14} />
            </button>
            
            {isAssistant && onFeedback && (
              <>
                <button
                  onClick={() => handleFeedback('positive')}
                  className="p-1 text-gray-400 hover:text-green-600 rounded transition-colors"
                  title={t('chat.thumbsUp')}
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  onClick={() => handleFeedback('negative')}
                  className="p-1 text-gray-400 hover:text-red-600 rounded transition-colors"
                  title={t('chat.thumbsDown')}
                >
                  <ThumbsDown size={14} />
                </button>
              </>
            )}
            
            {isAssistant && onRegenerate && (
              <button
                onClick={onRegenerate}
                className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                title={t('chat.regenerate')}
              >
                <RotateCcw size={14} />
              </button>
            )}
          </div>
        )}

        {/* Processing time */}
        {message.processing_time && (
          <div className="text-xs text-gray-400 mt-2">
            {t('chat.processedIn')} {message.processing_time}ms
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default ChatMessage
