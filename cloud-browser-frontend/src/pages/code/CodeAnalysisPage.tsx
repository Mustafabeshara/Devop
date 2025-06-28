
import { CodeBracketIcon } from '@heroicons/react/24/outline'

export function CodeAnalysisPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Code Analysis</h1>
        <p className="mt-1 text-gray-600">
          Analyze your code with Kimi-Dev-72B AI assistance
        </p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <CodeBracketIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No analyses yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start by analyzing a repository or code snippet.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
