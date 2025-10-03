import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { UserIcon, EnvelopeIcon, CalendarIcon } from '@heroicons/react/24/outline';
import { Navigate } from 'react-router-dom';

export const Profile: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-8">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center">
              <UserIcon className="w-10 h-10 text-primary-600" />
            </div>
            <div className="text-white">
              <h1 className="text-2xl font-bold">
                {user?.first_name && user?.last_name 
                  ? `${user.first_name} ${user.last_name}`
                  : user?.username
                }
              </h1>
              <p className="text-primary-100">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Profile Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Profile Information */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <UserIcon className="w-5 h-5 text-gray-400" />
                  <div>
                    <div className="text-sm text-gray-500">Username</div>
                    <div className="font-medium">{user?.username}</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <EnvelopeIcon className="w-5 h-5 text-gray-400" />
                  <div>
                    <div className="text-sm text-gray-500">Email</div>
                    <div className="font-medium">{user?.email}</div>
                    {user?.is_verified && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 ml-2">
                        Verified
                      </span>
                    )}
                  </div>
                </div>

                {user?.phone && (
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 flex items-center justify-center">📱</div>
                    <div>
                      <div className="text-sm text-gray-500">Phone</div>
                      <div className="font-medium">{user.phone}</div>
                    </div>
                  </div>
                )}

                <div className="flex items-center space-x-3">
                  <CalendarIcon className="w-5 h-5 text-gray-400" />
                  <div>
                    <div className="text-sm text-gray-500">Member since</div>
                    <div className="font-medium">
                      {new Date(user?.date_joined || '').toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Account Status */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Status</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Account Status</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    user?.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Email Verification</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    user?.is_verified 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {user?.is_verified ? 'Verified' : 'Pending'}
                  </span>
                </div>

                {user?.is_staff && (
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-blue-600">Staff Status</span>
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Staff Member
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Profile Completion</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${user?.profile_completion_percentage || 0}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium">
                      {user?.profile_completion_percentage || 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bio Section */}
          {user?.bio && (
            <div className="mt-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">About</h2>
              <p className="text-gray-600 leading-relaxed">{user.bio}</p>
            </div>
          )}

          {/* Actions */}
          <div className="mt-8 pt-6 border-t flex flex-col sm:flex-row gap-4">
            <Button variant="outline">
              Edit Profile
            </Button>
            <Button variant="outline">
              Change Password
            </Button>
            <Button variant="danger" onClick={handleLogout}>
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};