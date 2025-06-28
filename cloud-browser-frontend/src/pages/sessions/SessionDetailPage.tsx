
import { useParams } from 'react-router-dom'

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Session Details</h1>
        <p className="mt-1 text-gray-600">Session ID: {sessionId}</p>
      </div>

      <div className="card">
        <div className="card-body">
          <p className="text-gray-600">Session details will be displayed here.</p>
        </div>
      </div>
    </div>
  )
}
