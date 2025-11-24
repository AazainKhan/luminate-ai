import { useAuth } from "~/hooks/useAuth"
import { LoginForm } from "~/components/auth/LoginForm"
import { FileUpload } from "~/components/admin/FileUpload"
import { Settings, Upload, Database, BarChart3 } from "lucide-react"
import { useState, useEffect } from "react"
import { apiRequest } from "~/lib/api"
import "./style.css"

function AdminSidepanel() {
  const { user, role, loading, signOut } = useAuth()
  const [systemHealth, setSystemHealth] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<"upload" | "health">("upload")

  useEffect(() => {
    if (role === "admin") {
      loadSystemHealth()
      const interval = setInterval(loadSystemHealth, 10000) // Refresh every 10s
      return () => clearInterval(interval)
    }
  }, [role])

  const loadSystemHealth = async () => {
    try {
      const health = await apiRequest("/api/admin/health")
      setSystemHealth(health)
    } catch (error) {
      console.error("Error loading system health:", error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex flex-col h-screen">
        <div className="p-4 border-b">
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <p className="text-sm text-gray-600">Sign in to continue</p>
        </div>
        <div className="flex-1 overflow-auto">
          <LoginForm />
        </div>
      </div>
    )
  }

  // Only admins can access
  if (role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-4">
        <p className="text-gray-600 mb-4 text-center">
          Admin access required. Please sign in with an @centennialcollege.ca email.
        </p>
        <button
          onClick={signOut}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Sign Out
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            <p className="text-sm text-gray-600">{user.email}</p>
          </div>
          <button
            onClick={signOut}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900"
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="border-b bg-gray-50">
        <nav className="flex">
          <button
            onClick={() => setActiveTab("upload")}
            className={`px-4 py-3 text-sm font-medium ${
              activeTab === "upload"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Course Management
          </button>
          <button
            onClick={() => setActiveTab("health")}
            className={`px-4 py-3 text-sm font-medium ${
              activeTab === "health"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            System Health
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {activeTab === "upload" && (
            <>
              {/* Upload Section */}
              <div className="bg-white border rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Upload className="w-6 h-6 text-blue-600" />
                  <h2 className="text-xl font-semibold">Upload Course Materials</h2>
                </div>
                <p className="text-gray-600 mb-4">
                  Upload Blackboard export ZIP files or PDF documents to add course content.
                </p>
                <FileUpload />
              </div>
            </>
          )}

          {activeTab === "health" && (
            <>
              {/* System Health */}
              <div className="bg-white border rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <BarChart3 className="w-6 h-6 text-green-600" />
                  <h2 className="text-xl font-semibold">System Health</h2>
                </div>
                {systemHealth ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-600">ChromaDB</div>
                      <div
                        className={`text-2xl font-bold ${
                          systemHealth.chromadb?.status === "healthy"
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {systemHealth.chromadb?.status || "Unknown"}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {systemHealth.chromadb?.document_count || 0} documents
                      </div>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-600">ETL Jobs</div>
                      <div className="text-2xl font-bold">
                        {systemHealth.etl_jobs?.total || 0}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {systemHealth.etl_jobs?.completed || 0} completed
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-600">Loading system health...</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminSidepanel
