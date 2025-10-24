import React, { useState, useEffect } from 'react'

const ChatStorage = {
  // Сохранение чата в куки
  saveChat: (messages) => {
    try {
      const chatData = {
        messages: messages,
        timestamp: new Date().toISOString(),
        version: '1.0'
      }
      
      // Сохраняем в куки на 30 дней
      const cookieValue = encodeURIComponent(JSON.stringify(chatData))
      document.cookie = `chat_history=${cookieValue}; max-age=${30 * 24 * 60 * 60}; path=/`
      
      return true
    } catch (error) {
      console.error('Ошибка сохранения чата:', error)
      return false
    }
  },

  // Загрузка чата из куки
  loadChat: () => {
    try {
      const chatCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('chat_history='))
        ?.split('=')[1]
      
      if (chatCookie) {
        const chatData = JSON.parse(decodeURIComponent(chatCookie))
        
        // Проверяем версию и валидность данных
        if (chatData.version === '1.0' && chatData.messages) {
          // Конвертируем timestamp обратно в Date объекты
          const messages = chatData.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
          
          return messages
        }
      }
      
      return null
    } catch (error) {
      console.error('Ошибка загрузки чата:', error)
      return null
    }
  },

  // Очистка сохраненного чата
  clearChat: () => {
    document.cookie = 'chat_history=; max-age=0; path=/'
  },

  // Получение информации о сохраненном чате
  getChatInfo: () => {
    try {
      const chatCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('chat_history='))
        ?.split('=')[1]
      
      if (chatCookie) {
        const chatData = JSON.parse(decodeURIComponent(chatCookie))
        return {
          messageCount: chatData.messages?.length || 0,
          lastSaved: new Date(chatData.timestamp),
          version: chatData.version
        }
      }
      
      return null
    } catch (error) {
      console.error('Ошибка получения информации о чате:', error)
      return null
    }
  }
}

// Хук для работы с сохранением чата
export const useChatStorage = (initialMessages) => {
  const [messages, setMessages] = useState(initialMessages)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    // Загружаем сохраненный чат при инициализации
    const savedMessages = ChatStorage.loadChat()
    if (savedMessages && savedMessages.length > 0) {
      setMessages(savedMessages)
    }
    setIsLoaded(true)
  }, [])

  useEffect(() => {
    // Сохраняем чат при каждом изменении (кроме первого рендера)
    if (isLoaded && messages.length > 0) {
      ChatStorage.saveChat(messages)
    }
  }, [messages, isLoaded])

  const clearChat = () => {
    setMessages([{
      id: 1,
      text: "Привет! Я ваш RAG-ассистент. Как я могу помочь вам сегодня?",
      sender: 'bot',
      timestamp: new Date()
    }])
    ChatStorage.clearChat()
  }

  const getChatInfo = () => {
    return ChatStorage.getChatInfo()
  }

  return {
    messages,
    setMessages,
    clearChat,
    getChatInfo,
    isLoaded
  }
}

export default ChatStorage

