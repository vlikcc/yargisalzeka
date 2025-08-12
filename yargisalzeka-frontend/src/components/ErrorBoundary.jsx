import { Component } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { AlertTriangle, RefreshCw } from 'lucide-react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error: error,
      errorInfo: errorInfo
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen hero-gradient flex items-center justify-center p-4">
          <Card className="max-w-md w-full glass-card">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 p-3 bg-red-500 rounded-full w-16 h-16 flex items-center justify-center">
                <AlertTriangle className="h-8 w-8 text-white" />
              </div>
              <CardTitle className="text-white text-xl">Bir Hata Oluştu</CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-gray-300">
                Uygulamada beklenmeyen bir hata oluştu. Lütfen sayfayı yeniden yükleyerek tekrar deneyin.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="text-left bg-gray-800 p-3 rounded-md text-xs text-red-300 overflow-auto max-h-32">
                  <strong>Error:</strong> {this.state.error.toString()}
                  <br />
                  <strong>Stack:</strong> {this.state.errorInfo.componentStack}
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  onClick={this.handleReset}
                  variant="outline"
                  className="flex-1"
                >
                  Tekrar Dene
                </Button>
                <Button 
                  onClick={this.handleReload}
                  className="btn-primary flex-1"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Sayfayı Yenile
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
