
import { Link } from 'react-router-dom'
import {
  WindowIcon,
  CodeBracketIcon,
  PlayIcon,
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'

export function DashboardPage() {
  const { user } = useAuth()

  const quickActions = [
    {
      name: 'New Browser Session',
      description: 'Start a new isolated browser session',
      href: '/sessions?action=create',
      icon: WindowIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Code Analysis',
      description: 'Analyze code with Kimi-Dev-72B',
      href: '/code',
      icon: CodeBracketIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'View Sessions',
      description: 'Manage your browser sessions',
      href: '/sessions',
      icon: PlayIcon,
      color: 'bg-green-500',
    },
  ]

  const stats = [
    {
      name: 'Active Sessions',
      value: '2',
      icon: WindowIcon,
      change: '+1',
      changeType: 'increase',
    },
    {
      name: 'Total Session Time',
      value: '24.5h',
      icon: ClockIcon,
      change: '+2.1h',
      changeType: 'increase',
    },
    {
      name: 'Analyses Run',
      value: '12',
      icon: ChartBarIcon,
      change: '+3',
      changeType: 'increase',
    },
    {
      name: 'CPU Usage',
      value: '45%',
      icon: CpuChipIcon,
      change: '-5%',
      changeType: 'decrease',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-white shadow-soft rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.first_name || user?.username}!
            </h1>
            <p className="mt-1 text-gray-600">
              Manage your browser sessions and analyze code with AI assistance.
            </p>
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center space-x-2">
              <div className="status-indicator status-online">
                <div className="status-dot"></div>
                <span className="text-sm text-gray-600">All systems operational</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {stat.value}
                      </div>
                      <div
                        className={`ml-2 flex items-baseline text-sm font-semibold ${
                          stat.changeType === 'increase'
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {stat.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="card hover-lift group cursor-pointer"
            >
              <div className="card-body">
                <div className="flex items-center">
                  <div
                    className={`flex-shrink-0 w-10 h-10 ${action.color} rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}
                  >
                    <action.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-sm font-medium text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
                      {action.name}
                    </h3>
                    <p className="text-sm text-gray-500">{action.description}</p>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Sessions */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Recent Sessions</h3>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {[1, 2, 3].map((session) => (
                <div key={session} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <WindowIcon className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        Firefox Session #{session}
                      </p>
                      <p className="text-xs text-gray-500">Started 2 hours ago</p>
                    </div>
                  </div>
                  <div className="badge badge-success">Running</div>
                </div>
              ))}
            </div>
          </div>
          <div className="card-footer">
            <Link
              to="/sessions"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              View all sessions →
            </Link>
          </div>
        </div>

        {/* Recent Analyses */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Recent Analyses</h3>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {[1, 2, 3].map((analysis) => (
                <div key={analysis} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <CodeBracketIcon className="w-4 h-4 text-purple-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        Repository Analysis #{analysis}
                      </p>
                      <p className="text-xs text-gray-500">Completed 1 hour ago</p>
                    </div>
                  </div>
                  <div className="badge badge-primary">98% confidence</div>
                </div>
              ))}
            </div>
          </div>
          <div className="card-footer">
            <Link
              to="/code"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              View all analyses →
            </Link>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">System Information</h3>
        </div>
        <div className="card-body">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Type</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {user?.is_admin ? 'Administrator' : 'Standard User'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Max Containers</dt>
              <dd className="mt-1 text-sm text-gray-900">{user?.max_containers}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Session Timeout</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {Math.floor((user?.container_timeout || 3600) / 60)} minutes
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Preferred Browser</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">
                {user?.preferred_browser}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
