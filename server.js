const express = require('express')
const cors = require('cors')
const path = require('path')
const fs = require('fs').promises
const multer = require('multer')
const pdfParse = require('pdf-parse')
const mammoth = require('mammoth')

const app = express()
const PORT = process.env.PORT || 5000

// Middleware
app.use(cors())
app.use(express.json())

// Настройка multer для загрузки файлов
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'model_files')
    cb(null, uploadDir)
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname)
  }
})

const upload = multer({ storage })

// Функции для парсинга файлов
async function parsePDF(filePath) {
  try {
    const dataBuffer = await fs.readFile(filePath)
    const data = await pdfParse(dataBuffer)
    return data.text
  } catch (error) {
    throw new Error(`Ошибка парсинга PDF: ${error.message}`)
  }
}

async function parseWord(filePath) {
  try {
    const result = await mammoth.extractRawText({ path: filePath })
    return result.value
  } catch (error) {
    throw new Error(`Ошибка парсинга Word: ${error.message}`)
  }
}

async function parseCSV(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf-8')
    const lines = content.split('\n').filter(line => line.trim())
    
    if (lines.length < 2) {
      throw new Error('CSV файл должен содержать заголовки и хотя бы одну строку данных')
    }
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
    const requiredFields = ['название', 'цена', 'описание']
    
    // Проверяем наличие обязательных полей
    const missingFields = requiredFields.filter(field => 
      !headers.some(header => header.includes(field))
    )
    
    if (missingFields.length > 0) {
      throw new Error(`Отсутствуют обязательные поля: ${missingFields.join(', ')}`)
    }
    
    return content
  } catch (error) {
    throw new Error(`Ошибка валидации CSV: ${error.message}`)
  }
}

async function extractDataFromText(text, fileType) {
  // Простая логика извлечения данных из текста
  // В реальном проекте здесь должна быть более сложная логика
  const lines = text.split('\n').filter(line => line.trim())
  const products = []
  
  for (const line of lines) {
    // Ищем паттерны с ценами
    const priceMatch = line.match(/(\d+[\s,]*\d*)\s*руб/i)
    if (priceMatch) {
      const price = priceMatch[1].replace(/\s/g, '').replace(',', '')
      const name = line.replace(priceMatch[0], '').trim()
      
      if (name && price) {
        products.push({
          name: name,
          price: `${price} руб.`,
          description: line
        })
      }
    }
  }
  
  return products
}

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, 'dist')))

// API Routes
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body
    
    if (!message) {
      return res.status(400).json({ error: 'Сообщение не может быть пустым' })
    }

    // Интеграция с FastAPI для генерации ТКП
    let responseData
    try {
      responseData = await callFastAPI(message)
    } catch (error) {
      console.error('FastAPI недоступен, используем заглушку:', error)
      responseData = {
        text: await simulateRAGResponse(message),
        files: null
      }
    }
    
    res.json({ 
      response: responseData.text,
      files: responseData.files
    })
  } catch (error) {
    console.error('Ошибка при обработке сообщения:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
})

// Интеграция с FastAPI для генерации ТКП
async function callFastAPI(message) {
  try {
    const response = await fetch('http://localhost:8000/generate/both', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: message,
        top_k: 10,
        use_decomposition: true
      })
    })

    if (!response.ok) {
      throw new Error(`FastAPI error: ${response.status}`)
    }

    const data = await response.json()
    
    // Форматируем ответ для отображения в чате
    let responseText = data.search_result || 'ТКП сгенерировано успешно!'
    
    // Добавляем информацию о созданных файлах
    if (data.files) {
      responseText += '\n\n📄 Созданные документы:\n'
      if (data.files.word) {
        responseText += `• Word: ${data.files.word.filename}\n`
      }
      if (data.files.pdf) {
        responseText += `• PDF: ${data.files.pdf.filename}\n`
      }
    }
    
    return {
      text: responseText,
      files: data.files || null
    }
  } catch (error) {
    console.error('Ошибка FastAPI:', error)
    return {
      text: 'Извините, в данный момент сервис генерации ТКП недоступен. Попробуйте позже.',
      files: null
    }
  }
}

// Функция-заглушка для имитации RAG-ответа (если FastAPI недоступен)
async function simulateRAGResponse(message) {
  // Имитируем задержку обработки
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))
  
  // Простые ответы на основе ключевых слов
  const responses = {
    'привет': 'Привет! Я помогу вам найти нужные комплектующие. Что вы ищете?',
    'как дела': 'У меня всё отлично! Готов помочь вам с поиском комплектующих.',
    'спасибо': 'Пожалуйста! Рад был помочь. Есть ещё вопросы по комплектующим?',
    'пока': 'До свидания! Возвращайтесь, если понадобится помощь с поиском комплектующих.',
    'помощь': 'Я готов помочь! Задавайте вопросы о комплектующих, и я найду для вас нужную информацию.',
    'гайка': 'Для поиска гаек укажите размер (например: "гайка М6")',
    'болт': 'Для поиска болтов укажите размер (например: "болт М8х20")',
    'лоток': 'Для поиска лотков укажите размеры и тип (например: "лоток перфорированный 100x100")',
    'default': `Для поиска комплектующих опишите что вам нужно более подробно. Например: "гайка М6", "лоток 100x100 мм", "хомут для трубы 50 мм".`
  }
  
  const lowerMessage = message.toLowerCase()
  for (const [keyword, response] of Object.entries(responses)) {
    if (lowerMessage.includes(keyword)) {
      return response
    }
  }
  
  return responses.default
}

// Admin API endpoints
app.get('/api/admin/files', async (req, res) => {
  try {
    const files = await fs.readdir(modelFilesDir)
    const fileList = await Promise.all(
      files.map(async (filename) => {
        const filePath = path.join(modelFilesDir, filename)
        const stats = await fs.stat(filePath)
        return {
          name: filename,
          size: stats.size,
          modified: stats.mtime
        }
      })
    )
    res.json({ files: fileList })
  } catch (error) {
    console.error('Ошибка получения списка файлов:', error)
    res.status(500).json({ error: 'Ошибка получения списка файлов' })
  }
})

app.post('/api/admin/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Файл не был загружен' })
    }
    res.json({ message: 'Файл успешно загружен', filename: req.file.filename })
  } catch (error) {
    console.error('Ошибка загрузки файла:', error)
    res.status(500).json({ error: 'Ошибка загрузки файла' })
  }
})

app.get('/api/admin/files/:filename', async (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename)
    const filePath = path.join(modelFilesDir, filename)
    
    // Проверяем безопасность пути
    if (!filePath.startsWith(modelFilesDir)) {
      return res.status(400).json({ error: 'Недопустимое имя файла' })
    }
    
    const content = await fs.readFile(filePath, 'utf8')
    res.json({ content })
  } catch (error) {
    console.error('Ошибка чтения файла:', error)
    res.status(500).json({ error: 'Ошибка чтения файла' })
  }
})

app.put('/api/admin/files/:filename', async (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename)
    const filePath = path.join(modelFilesDir, filename)
    const { content } = req.body
    
    // Проверяем безопасность пути
    if (!filePath.startsWith(modelFilesDir)) {
      return res.status(400).json({ error: 'Недопустимое имя файла' })
    }
    
    await fs.writeFile(filePath, content, 'utf8')
    res.json({ message: 'Файл успешно сохранен' })
  } catch (error) {
    console.error('Ошибка сохранения файла:', error)
    res.status(500).json({ error: 'Ошибка сохранения файла' })
  }
})

app.delete('/api/admin/files/:filename', async (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename)
    const filePath = path.join(modelFilesDir, filename)
    
    // Проверяем безопасность пути
    if (!filePath.startsWith(modelFilesDir)) {
      return res.status(400).json({ error: 'Недопустимое имя файла' })
    }
    
    await fs.unlink(filePath)
    res.json({ message: 'Файл успешно удален' })
  } catch (error) {
    console.error('Ошибка удаления файла:', error)
    res.status(500).json({ error: 'Ошибка удаления файла' })
  }
})

app.post('/api/admin/rebuild', async (req, res) => {
  try {
    // Здесь будет логика пересборки модели
    // Пока что просто имитируем процесс
    console.log('Пересборка модели...')
    
    // Имитируем задержку
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    res.json({ message: 'Модель успешно пересобрана' })
  } catch (error) {
    console.error('Ошибка пересборки модели:', error)
    res.status(500).json({ error: 'Ошибка пересборки модели' })
  }
})

// CSV файлы endpoints
app.get('/api/admin/csv-files', async (req, res) => {
  try {
    const files = await fs.readdir(dataFilesDir)
    const csvFiles = files.filter(file => file.endsWith('.csv'))
    const fileList = await Promise.all(
      csvFiles.map(async (filename) => {
        const filePath = path.join(dataFilesDir, filename)
        const stats = await fs.stat(filePath)
        return {
          name: filename,
          size: stats.size,
          modified: stats.mtime
        }
      })
    )
    res.json({ files: fileList })
  } catch (error) {
    console.error('Ошибка получения списка CSV файлов:', error)
    res.status(500).json({ error: 'Ошибка получения списка CSV файлов' })
  }
})

// Новый endpoint для загрузки файлов с поддержкой разных режимов
app.post('/api/admin/upload-file', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Файл не был загружен' })
    }
    
    const file = req.file
    const mode = req.body.mode || 'append' // 'append' или 'replace'
    const fileExtension = path.extname(file.originalname).toLowerCase()
    
    // Проверяем поддерживаемые форматы
    const supportedFormats = ['.csv', '.pdf', '.docx']
    if (!supportedFormats.includes(fileExtension)) {
      await fs.unlink(file.path) // Удаляем временный файл
      return res.status(400).json({ 
        error: `Неподдерживаемый формат файла. Поддерживаются: ${supportedFormats.join(', ')}` 
      })
    }
    
    let processedData = null
    let csvContent = null
    
    try {
      // Парсим файл в зависимости от формата
      if (fileExtension === '.csv') {
        csvContent = await parseCSV(file.path)
      } else if (fileExtension === '.pdf') {
        const text = await parsePDF(file.path)
        const products = await extractDataFromText(text, 'pdf')
        csvContent = convertToCSV(products)
      } else if (fileExtension === '.docx') {
        const text = await parseWord(file.path)
        const products = await extractDataFromText(text, 'word')
        csvContent = convertToCSV(products)
      }
      
      // Сохраняем обработанные данные во временный CSV файл
      const tempCsvPath = path.join(uploadsDir, `processed_${Date.now()}.csv`)
      await fs.writeFile(tempCsvPath, csvContent, 'utf-8')
      
      // Уведомляем FastAPI о необходимости обновления БД
      const response = await fetch('http://localhost:8000/rebuild-db', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          csv_file: `processed_${Date.now()}.csv`,
          file_path: tempCsvPath,
          mode: mode
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log('База данных успешно обновлена:', result)
        
        // Удаляем временные файлы
        await fs.unlink(file.path)
        await fs.unlink(tempCsvPath)
        
        res.json({ 
          message: `Файл ${file.originalname} успешно обработан и база данных обновлена (режим: ${mode})`,
          filename: file.originalname,
          mode: mode,
          products_count: result.products_count || 0
        })
      } else {
        throw new Error('Ошибка обновления базы данных в FastAPI')
      }
      
    } catch (parseError) {
      // Удаляем временный файл при ошибке
      await fs.unlink(file.path)
      throw parseError
    }
    
  } catch (error) {
    console.error('Ошибка обработки файла:', error)
    res.status(500).json({ error: error.message || 'Ошибка обработки файла' })
  }
})

// Функция для конвертации данных в CSV формат
function convertToCSV(products) {
  if (!products || products.length === 0) {
    return 'название,цена,описание\n'
  }
  
  const headers = 'название,цена,описание\n'
  const rows = products.map(product => 
    `"${product.name}","${product.price}","${product.description}"`
  ).join('\n')
  
  return headers + rows
}

// Старый endpoint для обратной совместимости
app.post('/api/admin/upload-csv', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'CSV файл не был загружен' })
    }
    
    // Проверяем, что это CSV файл
    if (!req.file.originalname.endsWith('.csv')) {
      return res.status(400).json({ error: 'Файл должен быть в формате CSV' })
    }
    
    // Перемещаем файл в директорию данных
    const newPath = path.join(dataFilesDir, req.file.originalname)
    await fs.rename(req.file.path, newPath)
    
    // Уведомляем FastAPI о необходимости обновления БД
    try {
      const response = await fetch('http://localhost:8000/rebuild-db', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          csv_file: req.file.originalname,
          file_path: newPath
        })
      })
      
      if (response.ok) {
        console.log('База данных успешно обновлена')
      } else {
        console.log('Ошибка обновления базы данных в FastAPI')
      }
    } catch (apiError) {
      console.error('Ошибка вызова FastAPI для обновления БД:', apiError)
    }
    
    res.json({ message: 'CSV файл успешно загружен и база данных обновлена', filename: req.file.originalname })
  } catch (error) {
    console.error('Ошибка загрузки CSV файла:', error)
    res.status(500).json({ error: 'Ошибка загрузки CSV файла' })
  }
})

app.get('/api/admin/csv-files/:filename', async (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename)
    const filePath = path.join(dataFilesDir, filename)
    
    // Проверяем безопасность пути
    if (!filePath.startsWith(dataFilesDir)) {
      return res.status(400).json({ error: 'Недопустимое имя файла' })
    }
    
    const content = await fs.readFile(filePath, 'utf8')
    res.json({ content })
  } catch (error) {
    console.error('Ошибка чтения CSV файла:', error)
    res.status(500).json({ error: 'Ошибка чтения CSV файла' })
  }
})

app.delete('/api/admin/csv-files/:filename', async (req, res) => {
  try {
    const filename = decodeURIComponent(req.params.filename)
    const filePath = path.join(dataFilesDir, filename)
    
    // Проверяем безопасность пути
    if (!filePath.startsWith(dataFilesDir)) {
      return res.status(400).json({ error: 'Недопустимое имя файла' })
    }
    
    await fs.unlink(filePath)
    res.json({ message: 'CSV файл успешно удален' })
  } catch (error) {
    console.error('Ошибка удаления CSV файла:', error)
    res.status(500).json({ error: 'Ошибка удаления CSV файла' })
  }
})

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'RAG Chatbot API работает' })
})

// Catch all handler: send back React's index.html file for any non-API routes
// Endpoint для скачивания файлов
app.get('/api/download/:filename', async (req, res) => {
  try {
    const filename = req.params.filename
    const filePath = path.join(__dirname, 'generated_documents', filename)
    
    // Проверяем существование файла
    try {
      await fs.access(filePath)
    } catch (error) {
      return res.status(404).json({ error: 'Файл не найден' })
    }
    
    // Определяем MIME type по расширению
    const ext = path.extname(filename).toLowerCase()
    let mimeType = 'application/octet-stream'
    
    if (ext === '.pdf') {
      mimeType = 'application/pdf'
    } else if (ext === '.docx') {
      mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    // Отправляем файл
    res.setHeader('Content-Type', mimeType)
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`)
    res.sendFile(filePath)
    
  } catch (error) {
    console.error('Ошибка скачивания файла:', error)
    res.status(500).json({ error: 'Ошибка при скачивании файла' })
  }
})

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'))
})

app.listen(PORT, () => {
  console.log(`🚀 Сервер запущен на порту ${PORT}`)
  console.log(`📱 Веб-интерфейс доступен по адресу: http://localhost:${PORT}`)
  console.log(`🔗 API endpoint: http://localhost:${PORT}/api/chat`)
})
