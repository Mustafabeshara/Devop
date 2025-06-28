
import { UserIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'

export function ProfilePage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
        <p className="mt-1 text-gray-600">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Information */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">First Name</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      value={user?.first_name || ''} 
                      readOnly 
                    />
                  </div>
                  <div>
                    <label className="form-label">Last Name</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      value={user?.last_name || ''} 
                      readOnly 
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Email</label>
                  <input 
                    type="email" 
                    className="form-input" 
                    value={user?.email || ''} 
                    readOnly 
                  />
                </div>
                <div>
                  <label className="form-label">Username</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    value={user?.username || ''} 
                    readOnly 
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Account Info */}
        <div>
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">Account Info</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="flex items-center">
                  <UserIcon className="w-16 h-16 text-gray-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Account Type</p>
                  <p className="text-sm text-gray-600">
                    {user?.is_admin ? 'Administrator' : 'Standard User'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Member Since</p>
                  <p className="text-sm text-gray-600">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
