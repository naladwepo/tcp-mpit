import React from 'react'

const TypingIndicator = () => {
  return (
    <div className="flex justify-start">
      <div className="bot-message">
        <div className="typing-indicator">
          <div className="typing-dot" style={{ animationDelay: '0ms' }}></div>
          <div className="typing-dot" style={{ animationDelay: '150ms' }}></div>
          <div className="typing-dot" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator

