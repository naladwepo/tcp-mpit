import React, { useState, useEffect } from 'react'

const ThemeSwitcher = () => {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // Загружаем тему из куки
    const savedTheme = document.cookie
      .split('; ')
      .find(row => row.startsWith('theme='))
      ?.split('=')[1]
    
    if (savedTheme) {
      const isDarkTheme = savedTheme === 'dark'
      setIsDark(isDarkTheme)
      document.documentElement.classList.toggle('dark', isDarkTheme)
    } else {
      // Проверяем системную тему
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setIsDark(prefersDark)
      document.documentElement.classList.toggle('dark', prefersDark)
      // Сохраняем системную тему в куки
      const theme = prefersDark ? 'dark' : 'light'
      document.cookie = `theme=${theme}; max-age=${365 * 24 * 60 * 60}; path=/`
    }
  }, [])

  const toggleTheme = () => {
    const newIsDark = !isDark
    const newTheme = newIsDark ? 'dark' : 'light'
    
    setIsDark(newIsDark)
    
    // Сохраняем в куки на 1 год
    document.cookie = `theme=${newTheme}; max-age=${365 * 24 * 60 * 60}; path=/`
    
    // Принудительно применяем тему к документу
    document.documentElement.classList.toggle('dark', newIsDark)
  }

  return (
    <button
      onClick={toggleTheme}
      className="control-button"
      title={isDark ? 'Переключить на светлую тему' : 'Переключить на темную тему'}
    >
      {isDark ? (
        // Солнце для темной темы
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        // Луна для светлой темы
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  )
}

export default ThemeSwitcher
