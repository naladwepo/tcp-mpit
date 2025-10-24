import React from 'react'
import FileDownloadLinks from './FileDownloadLinks'

const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`chat-message ${isUser ? 'user-message' : 'bot-message'}`}>
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.text}
        </div>
        
        {/* Отображение файлов для скачивания */}
        {!isUser && message.files && (
          <FileDownloadLinks files={message.files} />
        )}
        
        <div className={`text-xs mt-2 opacity-70 ${isUser ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'}`}>
          {message.timestamp.toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
