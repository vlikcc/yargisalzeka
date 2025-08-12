import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  User, 
  Search, 
  Calendar, 
  Clock, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle,
  LogOut,
  Crown,
  Zap
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth.jsx'
import { apiService } from '../services/api.js'

const UserDashboard = ({ onClose }) => {
  const { user, logout, getAuthHeaders } = useAuth()
  const [usageData, setUsageData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchUsageData()
  }, [])

  const fetchUsageData = async () => {
    try {
      setIsLoading(true)
      const response = await apiService.getUserUsage(getAuthHeaders())
      setUsageData(response.data)
      setError('')
    } catch (error) {
      console.error('Error fetching usage data:', error)
      setError('Kullanım bilgileri alınamadı')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    onClose()
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Belirtilmemiş'
    try {
      return new Date(dateString).toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Geçersiz tarih'
    }
  }

  const getPlanBadgeColor = (plan) => {
    switch (plan) {
      case 'trial':
        return 'bg-blue-600 text-white'
      case 'temel':
        return 'bg-green-600 text-white'
      case 'standart':
        return 'bg-yellow-600 text-black'
      case 'premium':
        return 'bg-purple-600 text-white'
      default:
        return 'bg-gray-600 text-white'
    }
  }

  const getPlanIcon = (plan) => {
    switch (plan) {
      case 'trial':
        return <Zap className="h-4 w-4" />
      case 'premium':
        return <Crown className="h-4 w-4" />
      default:
        return <User className="h-4 w-4" />
    }
  }

  const getUsagePercentage = () => {
    if (!usageData?.usage_stats) return 0
    
    const stats = usageData.usage_stats
    if (stats.subscription_plan === 'trial') {
      const used = stats.trial_searches_used || 0
      const limit = stats.trial_searches_limit || 5
      return Math.round((used / limit) * 100)
    } else {
      const used = stats.monthly_searches_used || 0
      const limit = stats.monthly_search_limit || 0
      if (limit === 0) return 0
      return Math.round((used / limit) * 100)
    }
  }

  const getRemainingSearches = () => {
    if (!usageData?.usage_stats) return 0
    
    const stats = usageData.usage_stats
    if (stats.subscription_plan === 'trial') {
      const used = stats.trial_searches_used || 0
      const limit = stats.trial_searches_limit || 5
      return Math.max(0, limit - used)
    } else {
      const used = stats.monthly_searches_used || 0
      const limit = stats.monthly_search_limit || 0
      if (limit === 0) return 'Sınırsız'
      return Math.max(0, limit - used)
    }
  }

  const isTrialExpiringSoon = () => {
    if (!usageData?.usage_stats?.trial_end_date) return false
    
    const endDate = new Date(usageData.usage_stats.trial_end_date)
    const now = new Date()
    const hoursLeft = (endDate - now) / (1000 * 60 * 60)
    
    return hoursLeft <= 24 && hoursLeft > 0
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <Card className="w-full max-w-md bg-gray-900/95 border-gray-700">
          <CardContent className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mx-auto"></div>
            <p className="text-gray-300 mt-4">Yükleniyor...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl bg-gray-900/95 border-gray-700 max-h-[90vh] overflow-y-auto">
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="absolute right-0 top-0 text-gray-400 hover:text-white"
          >
            ✕
          </Button>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-600 rounded-full">
              <User className="h-6 w-6 text-black" />
            </div>
            <div>
              <CardTitle className="text-xl text-white">Kullanıcı Paneli</CardTitle>
              <CardDescription className="text-gray-300">
                Hesap bilgileriniz ve kullanım istatistikleriniz
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {error && (
            <div className="bg-red-500/20 border border-red-500/30 rounded-md p-3 flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-400" />
              <span className="text-red-200 text-sm">{error}</span>
            </div>
          )}

          {/* User Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Hesap Bilgileri</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Ad Soyad</label>
                <p className="text-white">{user?.full_name || 'Belirtilmemiş'}</p>
              </div>
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Email</label>
                <p className="text-white">{user?.email || 'Belirtilmemiş'}</p>
              </div>
            </div>
          </div>

          {/* Subscription Info */}
          {usageData?.usage_stats && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Abonelik Bilgileri</h3>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getPlanIcon(usageData.usage_stats.subscription_plan)}
                  <span className="text-white">Mevcut Plan:</span>
                </div>
                <Badge className={getPlanBadgeColor(usageData.usage_stats.subscription_plan)}>
                  {usageData.usage_stats.subscription_plan === 'trial' ? 'Ücretsiz Deneme' :
                   usageData.usage_stats.subscription_plan === 'temel' ? 'Temel Paket' :
                   usageData.usage_stats.subscription_plan === 'standart' ? 'Standart Paket' :
                   usageData.usage_stats.subscription_plan === 'premium' ? 'Premium Paket' : 'Ücretsiz'}
                </Badge>
              </div>

              {/* Trial specific info */}
              {usageData.usage_stats.subscription_plan === 'trial' && (
                <div className="bg-blue-500/20 border border-blue-500/30 rounded-md p-4 space-y-3">
                  <div className="flex items-center space-x-2">
                    <Zap className="h-4 w-4 text-blue-400" />
                    <span className="text-blue-200 font-medium">Ücretsiz Deneme Paketi</span>
                  </div>
                  
                  {isTrialExpiringSoon() && (
                    <div className="flex items-center space-x-2 text-yellow-300">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm">Deneme süreniz yakında sona eriyor!</span>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-blue-300">Başlangıç:</span>
                      <p className="text-white">{formatDate(usageData.usage_stats.trial_start_date)}</p>
                    </div>
                    <div>
                      <span className="text-blue-300">Bitiş:</span>
                      <p className="text-white">{formatDate(usageData.usage_stats.trial_end_date)}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Usage Statistics */}
          {usageData?.usage_stats && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Kullanım İstatistikleri</h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Kalan Arama Hakkı:</span>
                  <span className="text-white font-semibold">{getRemainingSearches()}</span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Kullanım Oranı</span>
                    <span className="text-gray-400">{getUsagePercentage()}%</span>
                  </div>
                  <Progress 
                    value={getUsagePercentage()} 
                    className="h-2"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-center p-3 bg-gray-800 rounded-md">
                    <Search className="h-5 w-5 text-yellow-400 mx-auto mb-1" />
                    <p className="text-gray-400">Kullanılan</p>
                    <p className="text-white font-semibold">
                      {usageData.usage_stats.subscription_plan === 'trial' 
                        ? usageData.usage_stats.trial_searches_used || 0
                        : usageData.usage_stats.monthly_searches_used || 0}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-gray-800 rounded-md">
                    <TrendingUp className="h-5 w-5 text-green-400 mx-auto mb-1" />
                    <p className="text-gray-400">Toplam Limit</p>
                    <p className="text-white font-semibold">
                      {usageData.usage_stats.subscription_plan === 'trial' 
                        ? usageData.usage_stats.trial_searches_limit || 5
                        : usageData.usage_stats.monthly_search_limit || 'Sınırsız'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-700">
            <Button
              onClick={fetchUsageData}
              variant="outline"
              className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
            >
              <TrendingUp className="mr-2 h-4 w-4" />
              Yenile
            </Button>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="flex-1 border-red-600 text-red-400 hover:bg-red-900/20"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Çıkış Yap
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default UserDashboard

