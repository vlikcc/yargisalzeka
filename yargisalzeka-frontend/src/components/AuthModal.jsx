import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { X, Eye, EyeOff, Mail, Lock, User, CheckCircle, AlertCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth.jsx'

const AuthModal = ({ isOpen, onClose, defaultTab = 'login' }) => {
  const [activeTab, setActiveTab] = useState(defaultTab)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  
  const { login: authLogin } = useAuth()

  // Login form state
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  })

  // Register form state
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  })

  const resetForms = () => {
    setLoginData({ email: '', password: '' })
    setRegisterData({ email: '', password: '', confirmPassword: '', full_name: '' })
    setMessage({ type: '', text: '' })
    setShowPassword(false)
    setShowConfirmPassword(false)
  }

  const handleClose = () => {
    resetForms()
    onClose()
  }

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validatePassword = (password) => {
    return password.length >= 6
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    
    if (!validateEmail(loginData.email)) {
      setMessage({ type: 'error', text: 'Geçerli bir email adresi girin.' })
      return
    }

    if (!validatePassword(loginData.password)) {
      setMessage({ type: 'error', text: 'Şifre en az 6 karakter olmalıdır.' })
      return
    }

    setIsLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const API_BASE_URL = 'https://yargisalzeka-api-77794337596.europe-west1.run.app/api/v1'
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginData.email,
          password: loginData.password
        })
      })

      const data = await response.json()

      if (response.ok && data.access_token) {
        // Use auth context to handle login
        // Create user_data from token or use a default structure
        const user_data = {
          user_id: data.user_id || 'unknown',
          email: loginData.email,
          subscription_plan: 'trial'
        }
        
        authLogin(user_data, data.access_token)
        
        setMessage({ type: 'success', text: 'Giriş başarılı! Yönlendiriliyorsunuz...' })
        
        // 2 saniye sonra modal'ı kapat
        setTimeout(() => {
          handleClose()
        }, 2000)
      } else {
        setMessage({ type: 'error', text: data.detail || 'Giriş yapılırken bir hata oluştu.' })
      }
    } catch (error) {
      console.error('Login error:', error)
      setMessage({ type: 'error', text: 'Sunucuya bağlanırken bir hata oluştu.' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()

    if (!validateEmail(registerData.email)) {
      setMessage({ type: 'error', text: 'Geçerli bir email adresi girin.' })
      return
    }

    if (!validatePassword(registerData.password)) {
      setMessage({ type: 'error', text: 'Şifre en az 6 karakter olmalıdır.' })
      return
    }

    if (registerData.password !== registerData.confirmPassword) {
      setMessage({ type: 'error', text: 'Şifreler eşleşmiyor.' })
      return
    }

    if (registerData.full_name.trim().length < 2) {
      setMessage({ type: 'error', text: 'Ad soyad en az 2 karakter olmalıdır.' })
      return
    }

    setIsLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const API_BASE_URL = 'https://yargisalzeka-api-77794337596.europe-west1.run.app/api/v1'
      
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: registerData.email,
          password: registerData.password,
          full_name: registerData.full_name
        })
      })

      const data = await response.json()

      if (response.ok && data.status === 'success') {
        setMessage({ 
          type: 'success', 
          text: 'Kayıt başarılı! 5 aramalık ücretsiz deneme paketiniz aktif edildi. Giriş yapabilirsiniz.' 
        })
        
        // 3 saniye sonra login sekmesine geç
        setTimeout(() => {
          setActiveTab('login')
          setMessage({ type: '', text: '' })
        }, 3000)
      } else {
        setMessage({ type: 'error', text: data.detail || 'Kayıt olurken bir hata oluştu.' })
      }
    } catch (error) {
      console.error('Register error:', error)
      setMessage({ type: 'error', text: 'Sunucuya bağlanırken bir hata oluştu.' })
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md bg-gray-900/95 border-gray-700">
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="absolute right-0 top-0 text-gray-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </Button>
          <CardTitle className="text-2xl text-center text-white">
            Yargısal Zeka
          </CardTitle>
          <CardDescription className="text-center text-gray-300">
            Hesabınıza giriş yapın veya yeni hesap oluşturun
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2 bg-gray-800">
              <TabsTrigger value="login" className="text-gray-300 data-[state=active]:bg-yellow-600 data-[state=active]:text-black">
                Giriş Yap
              </TabsTrigger>
              <TabsTrigger value="register" className="text-gray-300 data-[state=active]:bg-yellow-600 data-[state=active]:text-black">
                Kayıt Ol
              </TabsTrigger>
            </TabsList>

            {/* Message Display */}
            {message.text && (
              <div className={`mt-4 p-3 rounded-md flex items-center space-x-2 ${
                message.type === 'success' 
                  ? 'bg-green-500/20 border border-green-500/30 text-green-200' 
                  : 'bg-red-500/20 border border-red-500/30 text-red-200'
              }`}>
                {message.type === 'success' ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <span className="text-sm">{message.text}</span>
              </div>
            )}

            {/* Login Tab */}
            <TabsContent value="login" className="space-y-4 mt-6">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email" className="text-gray-300">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="ornek@email.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                      className="pl-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="login-password" className="text-gray-300">Şifre</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={loginData.password}
                      onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                      className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-white"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-yellow-600 hover:bg-yellow-700 text-black font-semibold"
                  disabled={isLoading}
                >
                  {isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
                </Button>
              </form>
            </TabsContent>

            {/* Register Tab */}
            <TabsContent value="register" className="space-y-4 mt-6">
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-name" className="text-gray-300">Ad Soyad</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="Adınız Soyadınız"
                      value={registerData.full_name}
                      onChange={(e) => setRegisterData({...registerData, full_name: e.target.value})}
                      className="pl-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-email" className="text-gray-300">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="ornek@email.com"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                      className="pl-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-password" className="text-gray-300">Şifre</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="En az 6 karakter"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                      className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-white"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-confirm-password" className="text-gray-300">Şifre Tekrar</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="register-confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Şifrenizi tekrar girin"
                      value={registerData.confirmPassword}
                      onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                      className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-white"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="bg-blue-500/20 border border-blue-500/30 rounded-md p-3">
                  <p className="text-blue-200 text-sm">
                    🎁 Kayıt olduğunuzda <strong>5 aramalık ücretsiz deneme</strong> paketiniz 3 gün süreyle aktif olacak!
                  </p>
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-yellow-600 hover:bg-yellow-700 text-black font-semibold"
                  disabled={isLoading}
                >
                  {isLoading ? 'Kayıt oluşturuluyor...' : 'Ücretsiz Hesap Oluştur'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

export default AuthModal

