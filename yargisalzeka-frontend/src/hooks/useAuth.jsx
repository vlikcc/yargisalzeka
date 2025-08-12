import { useState, useEffect, createContext, useContext } from 'react'
import { apiService } from '../services/api.js'

// Auth Context
const AuthContext = createContext()

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [token, setToken] = useState(null)

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('auth_token')
        const storedUser = localStorage.getItem('user_data')
        
        if (storedToken && storedUser) {
          setToken(storedToken)
          const parsed = JSON.parse(storedUser)
          setUser(parsed)
          // Kullanıcı bilgilerini /auth/me'den hydrate et (full_name ve plan için)
          try {
            const me = await apiService.getMe({
              'Authorization': `Bearer ${storedToken}`,
              'Content-Type': 'application/json'
            })
            if (me && me.full_name) {
              const hydrated = { ...parsed, full_name: me.full_name, email: me.email, subscription_plan: me.subscription_plan, user_id: me.id }
              setUser(hydrated)
              localStorage.setItem('user_data', JSON.stringify(hydrated))
            }
          } catch (e) {
            // sessizce geç
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        // Clear invalid data
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  // Login function
  const login = (userData, authToken) => {
    try {
      localStorage.setItem('auth_token', authToken)
      localStorage.setItem('user_data', JSON.stringify(userData))
      setToken(authToken)
      setUser(userData)
    } catch (error) {
      console.error('Error saving auth data:', error)
    }
  }

  // Logout function
  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    setToken(null)
    setUser(null)
  }

  // Check if user is authenticated
  const isAuthenticated = () => {
    return !!(token && user)
  }

  // Get auth headers for API calls
  const getAuthHeaders = () => {
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
    return {
      'Content-Type': 'application/json'
    }
  }

  const value = {
    user,
    token,
    isLoading,
    login,
    logout,
    isAuthenticated,
    getAuthHeaders
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default useAuth

