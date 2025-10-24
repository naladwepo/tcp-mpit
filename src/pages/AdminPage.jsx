import React, { useState, useEffect } from 'react'
import ThemeSwitcher from '../components/ThemeSwitcher'

const AdminPage = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [uploadMode, setUploadMode] = useState('append') // 'append' или 'replace'
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [supportedFormats, setSupportedFormats] = useState(['.csv', '.pdf', '.docx'])

  const handleLogin = (e) => {
    e.preventDefault()
    if (password === '1234') {
      setIsAuthenticated(true)
      setError('')
    } else {
      setError('Неверный пароль')
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Проверяем формат файла
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!supportedFormats.includes(fileExtension)) {
      setUploadStatus({ 
        type: 'error', 
        message: `Неподдерживаемый формат файла. Поддерживаются: ${supportedFormats.join(', ')}` 
      })
      return
    }

    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', uploadMode)

    try {
      const response = await fetch('/api/admin/upload-file', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        setUploadStatus({ 
          type: 'success', 
          message: `Файл ${file.name} успешно обработан! ${result.message}` 
        })
      } else {
        const errorData = await response.json()
        setUploadStatus({ 
          type: 'error', 
          message: errorData.error || 'Ошибка при обработке файла' 
        })
      }
    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: 'Ошибка при загрузке файла' 
      })
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setPassword('')
    setError('')
    setUploadStatus(null)
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
              🔐 Админ-панель
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Введите пароль для доступа
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Пароль
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Введите пароль"
                required
              />
            </div>

            {error && (
              <div className="bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 p-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-primary-500 text-white py-3 rounded-xl hover:bg-primary-600 transition-colors font-medium"
            >
              Войти
            </button>
          </form>

          <div className="mt-6 text-center">
            <a
              href="/"
              className="text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300"
            >
              ← Вернуться к чату
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 text-gray-900 dark:text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
              Админ-панель
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Управление базой данных и файлами
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <ThemeSwitcher />
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Выйти
            </button>
            <a
              href="/"
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              ← Вернуться к чату
            </a>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">
              Загрузка файлов
            </h2>

            {/* Режимы загрузки */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
                Режим загрузки:
              </h3>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="append"
                    checked={uploadMode === 'append'}
                    onChange={(e) => setUploadMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-gray-700 dark:text-gray-300">
                    Дополнение БД (добавить новые элементы)
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="replace"
                    checked={uploadMode === 'replace'}
                    onChange={(e) => setUploadMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-gray-700 dark:text-gray-300">
                    Перезапись БД (заменить все данные)
                  </span>
                </label>
              </div>
            </div>

            {/* Загрузка файла */}
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center mb-6">
              <input
                type="file"
                accept={supportedFormats.join(',')}
                onChange={handleFileUpload}
                disabled={uploading}
                className="w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-gray-700 dark:file:text-gray-300"
              />
              {uploading && (
                <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Обработка файла и обновление базы данных...
                </div>
              )}
            </div>

            {/* Статус загрузки */}
            {uploadStatus && (
              <div className={`p-4 rounded-lg mb-6 ${
                uploadStatus.type === 'success' 
                  ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' 
                  : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
              }`}>
                {uploadStatus.message}
              </div>
            )}

            {/* Информация о поддерживаемых форматах */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Поддерживаемые форматы:
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-sm">
                  <strong className="text-gray-800 dark:text-white">CSV:</strong>
                  <p className="text-gray-600 dark:text-gray-400">
                    Структурированные данные с колонками: название, цена, описание
                  </p>
                </div>
                <div className="text-sm">
                  <strong className="text-gray-800 dark:text-white">PDF:</strong>
                  <p className="text-gray-600 dark:text-gray-400">
                    Документы с таблицами и списками товаров
                  </p>
                </div>
                <div className="text-sm">
                  <strong className="text-gray-800 dark:text-white">Word:</strong>
                  <p className="text-gray-600 dark:text-gray-400">
                    Документы с таблицами и списками товаров
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminPage
