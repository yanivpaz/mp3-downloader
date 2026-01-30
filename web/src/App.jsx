import React, { useState, useEffect } from 'react'

export default function App() {
  const [url, setUrl] = useState('')
  const [output, setOutput] = useState('/mnt/c/mp3')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [jobId, setJobId] = useState(null)
  const [log, setLog] = useState('')

  useEffect(() => {
    let timer
    if (jobId) {
      timer = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:5000/status/${jobId}`)
          if (res.ok) {
            const data = await res.json()
            setLog(data.log_tail || '')
            if (!data.running) {
              setLoading(false)
              if (data.returncode === 0) {
                setMessage('Job finished successfully')
              } else if (data.returncode != null) {
                setMessage(`Job finished with return code ${data.returncode}`)
              } else {
                setMessage('Job finished')
              }
              clearInterval(timer)
            }
          } else {
            const txt = await res.text()
            setMessage('Error getting status: ' + txt)
            clearInterval(timer)
            setLoading(false)
          }
        } catch (err) {
          setMessage('Error polling status: ' + String(err))
          clearInterval(timer)
          setLoading(false)
        }
      }, 2000)
    }
    return () => clearInterval(timer)
  }, [jobId])

  async function startDownload(e) {
    e.preventDefault()
    setMessage('')
    setLog('')
    if (!url) {
      setMessage('Please provide a YouTube URL')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('http://localhost:5000/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, output })
      })
      const data = await res.json()
      if (res.status === 202) {
        setJobId(data.job_id)
        setMessage(`Download started (job ${data.job_id})`)
      } else {
        setMessage(data.error || JSON.stringify(data))
        setLoading(false)
      }
    } catch (err) {
      setMessage('Error: ' + String(err))
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>MP3 Downloader</h1>
      <form onSubmit={startDownload}>
        <label>
          YouTube URL
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://..." />
        </label>
        <label>
          Target folder
          <input value={output} onChange={e => setOutput(e.target.value)} />
        </label>
        <div className="row">
          <button type="submit" disabled={loading}>Download</button>
          {loading && <span className="spinner">Downloading...</span>}
        </div>
      </form>

      <div className="status">
        <p><strong>Status:</strong> {message}</p>
        {jobId && <p><strong>Job:</strong> {jobId}</p>}
        <pre className="log">{log}</pre>
      </div>

      <footer>
        <small>Backend: <code>http://localhost:5000</code></small>
      </footer>
    </div>
  )
}
