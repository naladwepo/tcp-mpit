import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ChatMessage from '../components/ChatMessage'
import MessageInput from '../components/MessageInput'
import TypingIndicator from '../components/TypingIndicator'
import ThemeSwitcher from '../components/ThemeSwitcher'
import { useChatStorage } from '../hooks/useChatStorage'

const ChatPage = () => {
  const initialMessages = [
    {
      id: 1,
      text: "Привет! Отправьте список материалов для формирования ТКП",
      sender: 'bot',
      timestamp: new Date()
    }
  ]
  
  const { messages, setMessages, clearChat, getChatInfo, isLoaded } = useChatStorage(initialMessages)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      // Здесь будет интеграция с RAG API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText })
      })

      if (!response.ok) {
        throw new Error('Ошибка при отправке сообщения')
      }

      const data = await response.json()
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.response || "Извините, произошла ошибка при обработке вашего сообщения.",
        sender: 'bot',
        timestamp: new Date(),
        files: data.files || null
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Ошибка:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: "Извините, в данный момент я не могу ответить. Попробуйте позже.",
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
              TKP Generator
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Генератор ТКП с использованием RAG
            </p>
          </div>

          {/* Chat Container */}
          <div className="chat-container">
            {/* Header */}
            
            {/* Messages Area */}
            <div className="messages-area">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="input-area">
              <div className="flex items-center justify-between mb-3">
                <div className="flex space-x-2">
                  <ThemeSwitcher />
                  <Link
                    to="/admin"
                    className="control-button"
                    title="Админ-панель"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </Link>
                  <button
                    onClick={() => {
                      if (confirm('Очистить историю чата?')) {
                        clearChat()
                      }
                    }}
                    className="control-button"
                    title="Очистить чат"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <div className="message-counter">
                  {messages.length - 1} сообщений
                  {getChatInfo() && (
                    <span className="ml-2">
                      • Сохранено: {getChatInfo().lastSaved.toLocaleDateString('ru-RU')}
                    </span>
                  )}
                </div>
              </div>
              <MessageInput onSendMessage={handleSendMessage} />
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-6 text-gray-500 dark:text-gray-400 text-sm">
            <p>Сделано с любовью командой [FTD]feel the dense</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
