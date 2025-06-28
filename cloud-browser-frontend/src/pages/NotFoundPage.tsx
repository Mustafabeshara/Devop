
import { Link } from 'react-router-dom'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md w-full">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center">
            <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
          </div>
          <h1 className="mt-6 text-3xl font-bold text-gray-900">404</h1>
          <p className="mt-2 text-lg text-gray-600">Page not found</p>
          <p className="mt-4 text-sm text-gray-500">
            Sorry, we couldn't find the page you're looking for.
          </p>
          <div className="mt-6">
            <Link
              to="/dashboard"
              className="btn btn-primary"
            >
              Go back home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
