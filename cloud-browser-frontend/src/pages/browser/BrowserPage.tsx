
import { useParams } from 'react-router-dom'

export function BrowserPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Browser Session</h1>
        <p className="mt-1 text-gray-600">Session ID: {sessionId}</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Browser session will be displayed here</p>
          </div>
        </div>
      </div>
    </div>
  )
}
