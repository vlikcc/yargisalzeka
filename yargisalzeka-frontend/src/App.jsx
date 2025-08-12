import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Brain, Search, FileText, Zap, CheckCircle, Star, Clock, Users, Scale, Cpu, Target, Award, User } from 'lucide-react'
import AuthModal from './components/AuthModal.jsx'
import UserDashboard from './components/UserDashboard.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import { AuthProvider, useAuth } from './hooks/useAuth.jsx'
import { apiService, ApiError } from './services/api.js'
import './App.css'

function AppContent() {
  const [caseText, setCaseText] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [keywords, setKeywords] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('search')
  const [authModal, setAuthModal] = useState({ isOpen: false, defaultTab: 'login' })
  const [showUserDashboard, setShowUserDashboard] = useState(false)

  const { user, isAuthenticated, getAuthHeaders } = useAuth()

  // Buton fonksiyonları
  const handleLogin = () => {
    if (isAuthenticated()) {
      setShowUserDashboard(true)
    } else {
      setAuthModal({ isOpen: true, defaultTab: 'login' })
    }
  }

  const handleFreeTrial = () => {
    if (isAuthenticated()) {
      setShowUserDashboard(true)
    } else {
      setAuthModal({ isOpen: true, defaultTab: 'register' })
    }
  }

  const handleWatchDemo = () => {
    alert('Demo video yakında eklenecek!')
    // TODO: Demo video modal'ı veya YouTube link'i
  }

  const handleSelectPlan = (planName) => {
    alert(`${planName} seçildi! Ödeme sayfasına yönlendiriliyorsunuz...`)
    // TODO: Ödeme sayfasına yönlendirme veya modal
  }

  const handleSmartSearch = async () => {
    if (!caseText.trim()) return
    
    // Check if user is authenticated
    if (!isAuthenticated()) {
      setError('Arama yapmak için giriş yapmanız gerekiyor.')
      setAuthModal({ isOpen: true, defaultTab: 'login' })
      return
    }
    
    setIsLoading(true)
    setError('')
    
    try {
      const response = await apiService.smartSearch(caseText, 10, getAuthHeaders())
      
      if (response.success) {
        setKeywords(response.keywords || [])
        setSearchResults(response.analyzed_results || [])
        setError('')
      } else {
        setError(response.message || 'Arama sırasında bir hata oluştu')
      }
    } catch (error) {
      console.error('Arama hatası:', error)
      
      if (error instanceof ApiError) {
        if (error.isAuthError()) {
          setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.')
          setAuthModal({ isOpen: true, defaultTab: 'login' })
        } else if (error.isUsageLimitError()) {
          setError(error.getUserMessage())
        } else {
          setError(error.getUserMessage())
        }
      } else {
        setError('Sunucuya bağlanırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const subscriptionPlans = [
    {
      name: 'Temel Paket',
      price: '99 TL',
      period: 'aylık',
      searches: '50 arama',
      features: [
        'Anahtar Kelime Çıkarma',
        'AI Destekli Karar Analizi',
        'Temel Destek'
      ],
      popular: false
    },
    {
      name: 'Standart Paket',
      price: '299 TL',
      period: 'aylık',
      searches: '500 arama',
      features: [
        'Anahtar Kelime Çıkarma',
        'AI Destekli Karar Analizi',
        'Dilekçe Şablonu (10 adet/ay)',
        'Öncelikli Destek'
      ],
      popular: true
    },
    {
      name: 'Premium Paket',
      price: '999 TL',
      period: 'aylık',
      searches: 'Sınırsız',
      features: [
        'Anahtar Kelime Çıkarma',
        'AI Destekli Karar Analizi',
        'Sınırsız Dilekçe Şablonu',
        '7/24 Premium Destek',
        'API Erişimi'
      ],
      popular: false
    }
  ]

  return (
    <div className="min-h-screen hero-gradient">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <img 
                src="/yargisalzeka-logo.png" 
                alt="Yargısal Zeka Logo" 
                className="h-12 w-auto"
              />
              <div>
                <h1 className="text-2xl font-bold text-white">YARGISAL ZEKA</h1>
                <p className="text-sm gold-text">Yapay Zeka Destekli Yargıtay Kararı Arama Platformu</p>
              </div>
            </div>
            <nav className="hidden md:flex space-x-6">
              <Button 
                variant="ghost" 
                onClick={() => setActiveTab('search')}
                className="text-white hover:text-yellow-400 hover:bg-white/10"
              >
                Ana Sayfa
              </Button>
              <Button 
                variant="ghost" 
                onClick={() => setActiveTab('pricing')}
                className="text-white hover:text-yellow-400 hover:bg-white/10"
              >
                Fiyatlandırma
              </Button>
              <Button 
                variant="ghost" 
                onClick={() => setActiveTab('about')}
                className="text-white hover:text-yellow-400 hover:bg-white/10"
              >
                Özellikler
              </Button>
              <Button className="btn-primary" onClick={handleLogin}>
                {isAuthenticated() ? (
                  <div className="flex items-center space-x-2">
                    <User className="h-4 w-4" />
                    <span className="hidden sm:inline">{user?.full_name?.split(' ')[0] || 'Kullanıcı'}</span>
                  </div>
                ) : (
                  'Giriş Yap'
                )}
              </Button>
            </nav>
            
            {/* Mobile Navigation */}
            <div className="md:hidden">
              <Button className="btn-primary" onClick={handleLogin}>
                {isAuthenticated() ? (
                  <User className="h-4 w-4" />
                ) : (
                  'Giriş'
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3 bg-black/20 border border-white/10">
            <TabsTrigger value="search" className="text-white data-[state=active]:bg-yellow-600 data-[state=active]:text-black">
              Akıllı Arama
            </TabsTrigger>
            <TabsTrigger value="pricing" className="text-white data-[state=active]:bg-yellow-600 data-[state=active]:text-black">
              Abonelik Planları
            </TabsTrigger>
            <TabsTrigger value="about" className="text-white data-[state=active]:bg-yellow-600 data-[state=active]:text-black">
              Platform Özellikleri
            </TabsTrigger>
          </TabsList>

          {/* Akıllı Arama Sekmesi */}
          <TabsContent value="search" className="space-y-8">
            {/* Hero Section */}
            <div className="text-center py-16 animate-fade-in-up">
              <h2 className="hero-title mb-6">
                HUKUK ARAŞTIRMALARINDA
                <span className="block gold-gradient">DEVRİM</span>
              </h2>
              <p className="hero-subtitle max-w-4xl mx-auto mb-8">
                Yapay zeka destekli platformumuz ile Yargıtay kararlarını saniyeler içinde bulun, 
                analiz edin ve dilekçelerinize entegre edin.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="btn-primary px-8 py-4 text-lg pulse-gold" onClick={handleFreeTrial}>
                  <Brain className="mr-2 h-5 w-5" />
                  Ücretsiz Deneyin
                </Button>
                <Button size="lg" className="btn-secondary px-8 py-4 text-lg" onClick={handleWatchDemo}>
                  <FileText className="mr-2 h-5 w-5" />
                  Demo İzleyin
                </Button>
              </div>
            </div>

            {/* Özellik Kartları */}
            <div className="grid md:grid-cols-3 gap-8 mb-12">
              <Card className="feature-card animate-fade-in-up">
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 p-3 bg-yellow-600 rounded-full w-16 h-16 flex items-center justify-center">
                    <Brain className="h-8 w-8 text-black" />
                  </div>
                  <CardTitle className="text-white text-xl">AI Destekli Analiz</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-gray-300">
                    Google Gemini AI ile olay metinlerinden otomatik anahtar kelime çıkarma ve karar analizi
                  </p>
                </CardContent>
              </Card>

              <Card className="feature-card animate-fade-in-up">
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 p-3 bg-blue-500 rounded-full w-16 h-16 flex items-center justify-center">
                    <Zap className="h-8 w-8 text-white" />
                  </div>
                  <CardTitle className="text-white text-xl">Paralel Arama</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-gray-300">
                    Çoklu anahtar kelimelerle eş zamanlı arama yaparak sonuçları 60x daha hızlı getirir
                  </p>
                </CardContent>
              </Card>

              <Card className="feature-card animate-fade-in-up">
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 p-3 bg-purple-500 rounded-full w-16 h-16 flex items-center justify-center">
                    <Target className="h-8 w-8 text-white" />
                  </div>
                  <CardTitle className="text-white text-xl">Akıllı Puanlama</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-gray-300">
                    Bulunan kararları olay metniyle ilişkisine göre puanlayarak %90 doğruluk oranı sağlar
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Arama Formu */}
            <Card className="max-w-4xl mx-auto glass-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-white">
                  <Search className="h-5 w-5 text-yellow-400" />
                  <span>Olay Metninizi Girin</span>
                </CardTitle>
                <CardDescription className="text-gray-300">
                  Hukuki durumunuzu detaylı olarak açıklayın. AI sistemimiz otomatik olarak 
                  anahtar kelimeleri çıkaracak ve en alakalı Yargıtay kararlarını bulacak.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Örnek: Müvekkilim A şirketi ile B şirketi arasında imzalanan satış sözleşmesinde, B şirketi teslim tarihini geçirmesi nedeniyle tazminat talep etmekteyiz..."
                  value={caseText}
                  onChange={(e) => setCaseText(e.target.value)}
                  rows={6}
                  className="w-full bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                />
                <Button 
                  onClick={handleSmartSearch}
                  disabled={!caseText.trim() || isLoading}
                  className="w-full btn-primary"
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <Clock className="mr-2 h-4 w-4 animate-spin" />
                      AI Analiz Ediyor...
                    </>
                  ) : (
                    <>
                      <Brain className="mr-2 h-4 w-4" />
                      Akıllı Arama Başlat
                    </>
                  )}
                </Button>
                {error && (
                  <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-md">
                    <p className="text-red-200 text-sm">{error}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Anahtar Kelimeler */}
            {keywords.length > 0 && (
              <Card className="max-w-4xl mx-auto glass-card">
                <CardHeader>
                  <CardTitle className="text-white">Çıkarılan Anahtar Kelimeler</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {keywords.map((keyword, index) => (
                      <Badge key={index} className="bg-yellow-600 text-black hover:bg-yellow-500">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Arama Sonuçları */}
            {searchResults.length > 0 && (
              <div className="max-w-4xl mx-auto space-y-4">
                <h3 className="text-2xl font-bold text-white">
                  Bulunan Yargıtay Kararları ({searchResults.length})
                </h3>
                {searchResults.map((result, index) => (
                  <Card key={index} className="glass-card hover:border-yellow-400/50 transition-all">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-lg text-white">{result.title || `Karar ${index + 1}`}</CardTitle>
                        <div className="flex items-center space-x-2">
                          <Badge className={`${result.ai_score > 70 ? "bg-green-600" : result.ai_score > 40 ? "bg-yellow-600 text-black" : "bg-gray-600"}`}>
                            AI Skoru: {result.ai_score}/100
                          </Badge>
                          {result.ai_score > 70 && <Star className="h-4 w-4 text-yellow-400" />}
                        </div>
                      </div>
                      <CardDescription className="text-gray-300">{result.ai_explanation}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-300 mb-2">
                        <strong>Benzerlik:</strong> {result.ai_similarity}
                      </p>
                      <p className="text-sm text-gray-200 line-clamp-3">
                        {result.content?.substring(0, 300)}...
                      </p>
                      <div className="mt-4 flex space-x-2">
                        <Button size="sm" className="btn-secondary">
                          <FileText className="mr-2 h-4 w-4" />
                          Detayları Gör
                        </Button>
                        <Button size="sm" className="btn-primary">
                          Dilekçeye Ekle
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Abonelik Planları Sekmesi */}
          <TabsContent value="pricing" className="space-y-8">
            <div className="text-center py-12">
              <h2 className="hero-title mb-4">ABONELİK PLANLARI</h2>
              <p className="hero-subtitle">
                İhtiyacınıza uygun planı seçin ve hukuki araştırmalarınızı hızlandırın
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {subscriptionPlans.map((plan, index) => (
                <Card key={index} className={`feature-card relative ${plan.popular ? 'border-yellow-400 scale-105' : ''}`}>
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-yellow-600 text-black">En Popüler</Badge>
                    </div>
                  )}
                  <CardHeader className="text-center">
                    <CardTitle className="text-2xl text-white">{plan.name}</CardTitle>
                    <div className="text-4xl font-bold gold-text">
                      {plan.price}
                      <span className="text-lg text-gray-400">/{plan.period}</span>
                    </div>
                    <CardDescription className="text-lg text-gray-300">{plan.searches}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <ul className="space-y-3">
                      {plan.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center space-x-2">
                          <CheckCircle className="h-5 w-5 text-green-400" />
                          <span className="text-gray-300">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button 
                      className={`w-full ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => handleSelectPlan(plan.name)}
                    >
                      Planı Seç
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Platform Özellikleri Sekmesi */}
          <TabsContent value="about" className="space-y-8">
            <div className="text-center py-12">
              <h2 className="hero-title mb-4">PLATFORM ÖZELLİKLERİ</h2>
              <p className="hero-subtitle">
                Hukuk profesyonellerinin ihtiyaçları için özel olarak tasarlanmış özellikler
              </p>
            </div>

            {/* Ana Özellikler */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <Card className="feature-card text-center">
                <CardHeader>
                  <img 
                    src="/ai-brain-analysis.png" 
                    alt="AI Analiz" 
                    className="w-20 h-20 mx-auto mb-4 rounded-lg"
                  />
                  <CardTitle className="text-white">Yapay Zeka Destekli Analiz</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-300">
                    Google Gemini AI ile olay metinlerinden otomatik anahtar kelime çıkarma ve karar analizi
                  </p>
                </CardContent>
              </Card>

              <Card className="feature-card text-center">
                <CardHeader>
                  <img 
                    src="/parallel-search-tech.png" 
                    alt="Paralel Arama" 
                    className="w-20 h-20 mx-auto mb-4 rounded-lg"
                  />
                  <CardTitle className="text-white">Paralel Arama Teknolojisi</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-300">
                    Çoklu anahtar kelimelerle eş zamanlı arama yaparak sonuçları hızlı bir şekilde getirir
                  </p>
                </CardContent>
              </Card>

              <Card className="feature-card text-center">
                <CardHeader>
                  <img 
                    src="/smart-scoring-system.png" 
                    alt="Akıllı Puanlama" 
                    className="w-20 h-20 mx-auto mb-4 rounded-lg"
                  />
                  <CardTitle className="text-white">Akıllı Puanlama Sistemi</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-300">
                    Bulunan kararları olay metniyle ilişkisine göre puanlayarak en alakalı sonuçları öne çıkarır
                  </p>
                </CardContent>
              </Card>

              <Card className="feature-card text-center">
                <CardHeader>
                  <FileText className="h-16 w-16 text-green-400 mx-auto mb-4" />
                  <CardTitle className="text-white">Otomatik Dilekçe Şablonları</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-300">
                    Seçilen Yargıtay kararlarını referans alan dilekçe şablonları oluşturur
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Sistem Avantajları */}
            <Card className="max-w-6xl mx-auto glass-card">
              <CardHeader>
                <CardTitle className="text-white text-2xl text-center">Sistem Avantajları</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                  <div className="text-center">
                    <div className="bg-yellow-600 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                      <span className="text-3xl font-bold text-black">60x</span>
                    </div>
                    <h4 className="font-semibold mb-2 text-white">Daha Hızlı</h4>
                    <p className="text-sm text-gray-300">
                      Geleneksel yöntemlere göre 60 kat daha hızlı sonuç
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="bg-green-500 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                      <span className="text-3xl font-bold text-white">90%</span>
                    </div>
                    <h4 className="font-semibold mb-2 text-white">Doğruluk Oranı</h4>
                    <p className="text-sm text-gray-300">
                      En alakalı kararları bulma başarı oranı
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="bg-blue-500 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                      <span className="text-3xl font-bold text-white">5</span>
                    </div>
                    <h4 className="font-semibold mb-2 text-white">Dakika</h4>
                    <p className="text-sm text-gray-300">
                      Kapsamlı araştırma için gereken süre
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="bg-purple-500 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                      <Award className="h-10 w-10 text-white" />
                    </div>
                    <h4 className="font-semibold mb-2 text-white">Premium Kalite</h4>
                    <p className="text-sm text-gray-300">
                      Enterprise seviyede güvenilirlik ve performans
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-black/30 border-t border-white/10 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white font-semibold mb-4">Yargısal Zeka</h3>
              <p className="text-gray-400 text-sm">
                Yapay zeka destekli hukuk araştırma platformu
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Ürün</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Özellikler</li>
                <li>Fiyatlandırma</li>
                <li>API</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Destek</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Yardım Merkezi</li>
                <li>İletişim</li>
                <li>Dokümantasyon</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Şirket</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>Hakkımızda</li>
                <li>Gizlilik</li>
                <li>Şartlar</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 mt-8 pt-8 text-center">
            <p className="text-gray-400 text-sm">
              © 2024 Yargısal Zeka. Tüm hakları saklıdır.
            </p>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={authModal.isOpen}
        onClose={() => setAuthModal({ isOpen: false, defaultTab: 'login' })}
        defaultTab={authModal.defaultTab}
      />

      {/* User Dashboard */}
      {showUserDashboard && (
        <UserDashboard onClose={() => setShowUserDashboard(false)} />
      )}
    </div>
  )
}

// Main App component with ErrorBoundary and AuthProvider
function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

