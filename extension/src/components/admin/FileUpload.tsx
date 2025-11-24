import { useState, useRef } from "react"
import { Upload, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react"
import { apiRequest } from "~/lib/api"

interface ETLJob {
  job_id: string
  filename: string
  status: "processing" | "completed" | "error"
  progress: number
  message: string
  error?: string
}

export function FileUpload() {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [jobs, setJobs] = useState<ETLJob[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0])
    }
  }

  const uploadFile = async (file: File) => {
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const token = await (await import("~/lib/supabase")).supabase.auth.getSession().then(
        ({ data: { session } }) => session?.access_token || null
      )

      const response = await fetch("http://localhost:8000/api/admin/upload", {
        method: "POST",
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      setJobs((prev) => [result, ...prev])

      // Poll for status updates
      pollJobStatus(result.job_id)
    } catch (error: any) {
      console.error("Upload error:", error)
      alert(`Upload failed: ${error.message}`)
    } finally {
      setUploading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await apiRequest<ETLJob>(`/api/admin/etl/status/${jobId}`)
        setJobs((prev) =>
          prev.map((job) => (job.job_id === jobId ? status : job))
        )

        if (status.status === "completed" || status.status === "error") {
          clearInterval(interval)
        }
      } catch (error) {
        console.error("Error polling job status:", error)
        clearInterval(interval)
      }
    }, 2000) // Poll every 2 seconds
  }

  return (
    <div className="space-y-4">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-white"
        }`}
      >
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 mb-2">
          Drag and drop files here, or click to browse
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Supports .zip (Blackboard exports) and .pdf files
        </p>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Uploading...</span>
            </>
          ) : (
            <span>Select Files</span>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.pdf"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {jobs.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold">Upload Status</h3>
          {jobs.map((job) => (
            <div
              key={job.job_id}
              className="border rounded-lg p-4 bg-white"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {job.status === "processing" && (
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  )}
                  {job.status === "completed" && (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  )}
                  {job.status === "error" && (
                    <AlertCircle className="w-4 h-4 text-red-600" />
                  )}
                  <span className="font-medium">{job.filename}</span>
                </div>
                <span
                  className={`text-sm px-2 py-1 rounded ${
                    job.status === "completed"
                      ? "bg-green-100 text-green-800"
                      : job.status === "error"
                      ? "bg-red-100 text-red-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {job.status}
                </span>
              </div>
              {job.status === "processing" && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{job.message}</p>
                </div>
              )}
              {job.status === "completed" && (
                <p className="text-sm text-green-600 mt-1">{job.message}</p>
              )}
              {job.status === "error" && job.error && (
                <p className="text-sm text-red-600 mt-1">{job.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

