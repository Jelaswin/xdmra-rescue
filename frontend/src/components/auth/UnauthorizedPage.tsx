import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function UnauthorizedPage() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-slate-800 mb-2">Access Denied</h1>
        <p className="text-slate-600 mb-6">
          You don't have permission to access this page.
        </p>

        {user && (
          <div className="bg-slate-50 rounded-md p-4 mb-6 text-left">
            <p className="text-sm text-slate-600">
              <span className="font-medium">Logged in as:</span> {user.full_name}
            </p>
            <p className="text-sm text-slate-600">
              <span className="font-medium">Role:</span> {user.role}
            </p>
          </div>
        )}

        <div className="flex flex-col space-y-3">
          <Link
            to="/"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700"
          >
            Go to Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="w-full bg-slate-200 text-slate-700 py-2 px-4 rounded-md font-medium hover:bg-slate-300"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}