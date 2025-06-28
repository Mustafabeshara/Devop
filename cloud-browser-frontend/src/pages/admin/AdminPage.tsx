
import { ShieldCheckIcon } from '@heroicons/react/24/outline'

export function AdminPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-1 text-gray-600">
          System administration and management
        </p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Admin Dashboard</h3>
            <p className="mt-1 text-sm text-gray-500">
              Administrative features will be available here.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
