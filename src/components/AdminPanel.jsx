import React, { useState, useEffect } from 'react'

const AdminPanel = ({ isOpen, onClose }) => {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [editingFile, setEditingFile] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadFiles()
    }
  }, [isOpen])

  const loadFiles = async () => {
    try {
      const response = await fetch('/api/admin/files')
      const data = await response.json()
      setFiles(data.files || [])
    } catch (error) {
      console.error('Ошибка загрузки файлов:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/admin/upload', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        await loadFiles()
        alert('Файл успешно загружен!')
      } else {
        alert('Ошибка при загрузке файла')
      }
    } catch (error) {
      console.error('Ошибка загрузки:', error)
      alert('Ошибка при загрузке файла')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleFileSelect = async (filename) => {
    try {
      const response = await fetch(`/api/admin/files/${encodeURIComponent(filename)}`)
      const data = await response.json()
      
      setSelectedFile(filename)
      setFileContent(data.content)
      setEditingFile(null)
    } catch (error) {
      console.error('Ошибка загрузки файла:', error)
      alert('Ошибка при загрузке файла')
    }
  }

  const handleFileEdit = () => {
    setEditingFile(selectedFile)
  }

  const handleFileSave = async () => {
    if (!editingFile || !fileContent) return

    try {
      const response = await fetch(`/api/admin/files/${encodeURIComponent(editingFile)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: fileContent })
      })

      if (response.ok) {
        setEditingFile(null)
        alert('Файл успешно сохранен!')
      } else {
        alert('Ошибка при сохранении файла')
      }
    } catch (error) {
      console.error('Ошибка сохранения:', error)
      alert('Ошибка при сохранении файла')
    }
  }

  const handleFileDelete = async (filename) => {
    if (!confirm(`Удалить файл "${filename}"?`)) return

    try {
      const response = await fetch(`/api/admin/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        await loadFiles()
        if (selectedFile === filename) {
          setSelectedFile(null)
          setFileContent('')
        }
        alert('Файл успешно удален!')
      } else {
        alert('Ошибка при удалении файла')
      }
    } catch (error) {
      console.error('Ошибка удаления:', error)
      alert('Ошибка при удалении файла')
    }
  }

  const handleRebuildModel = async () => {
    if (!confirm('Пересобрать модель? Это может занять некоторое время.')) return

    try {
      const response = await fetch('/api/admin/rebuild', {
        method: 'POST'
      })

      if (response.ok) {
        alert('Модель успешно пересобрана!')
      } else {
        alert('Ошибка при пересборке модели')
      }
    } catch (error) {
      console.error('Ошибка пересборки:', error)
      alert('Ошибка при пересборке модели')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-xl w-full max-w-6xl mx-4 h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
            Админ-панель - Управление файлами модели
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar - Список файлов */}
          <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
            <div className="space-y-4">
              {/* Загрузка файла */}
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                />
                {uploading && (
                  <div className="mt-2 text-sm text-gray-500">Загрузка...</div>
                )}
              </div>

              {/* Список файлов */}
              <div>
                <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Файлы модели ({files.length})
                </h4>
                <div className="space-y-1">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className={`p-2 rounded cursor-pointer flex justify-between items-center ${
                        selectedFile === file.name
                          ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                      onClick={() => handleFileSelect(file.name)}
                    >
                      <span className="text-sm truncate">{file.name}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleFileDelete(file.name)
                        }}
                        className="text-red-500 hover:text-red-700 text-xs"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Действия */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={handleRebuildModel}
                  className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors"
                >
                  Пересобрать модель
                </button>
              </div>
            </div>
          </div>

          {/* Main content - Редактор файла */}
          <div className="flex-1 flex flex-col">
            {selectedFile ? (
              <>
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">
                    {selectedFile}
                  </h4>
                  <div className="space-x-2">
                    {!editingFile ? (
                      <button
                        onClick={handleFileEdit}
                        className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                      >
                        Редактировать
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={() => setEditingFile(null)}
                          className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
                        >
                          Отмена
                        </button>
                        <button
                          onClick={handleFileSave}
                          className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                        >
                          Сохранить
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex-1 p-4">
                  {editingFile ? (
                    <textarea
                      value={fileContent}
                      onChange={(e) => setFileContent(e.target.value)}
                      className="w-full h-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-white resize-none"
                      placeholder="Содержимое файла..."
                    />
                  ) : (
                    <pre className="w-full h-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white overflow-auto whitespace-pre-wrap">
                      {fileContent}
                    </pre>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
                <div className="text-center">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p>Выберите файл для просмотра и редактирования</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminPanel

