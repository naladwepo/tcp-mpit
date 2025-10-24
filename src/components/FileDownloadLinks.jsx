import React from 'react'

const FileDownloadLinks = ({ files }) => {
  if (!files) return null

  const handleDownload = (filename) => {
    const link = document.createElement('a')
    link.href = `/api/download/${filename}`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
      <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-3">
        📄 Скачать документы:
      </h4>
      <div className="flex flex-wrap gap-2">
        {files.word && (
          <button
            onClick={() => handleDownload(files.word.filename)}
            className="px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Word (.docx)
          </button>
        )}
        {files.pdf && (
          <button
            onClick={() => handleDownload(files.pdf.filename)}
            className="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            PDF (.pdf)
          </button>
        )}
      </div>
    </div>
  )
}

export default FileDownloadLinks
