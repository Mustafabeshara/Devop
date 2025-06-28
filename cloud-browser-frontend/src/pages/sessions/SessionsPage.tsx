
import { PlusIcon, WindowIcon } from '@heroicons/react/24/outline'

export function SessionsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Browser Sessions</h1>
          <p className="mt-1 text-gray-600">
            Manage your isolated browser sessions
          </p>
        </div>
        <button className="btn btn-primary">
          <PlusIcon className="w-4 h-4 mr-2" />
          New Session
        </button>
      </div>

      {/* Sessions List */}
      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <WindowIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No sessions</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new browser session.
            </p>
            <div className="mt-6">
              <button className="btn btn-primary">
                <PlusIcon className="w-4 h-4 mr-2" />
                New Session
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
