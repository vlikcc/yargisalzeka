// API Service Layer
const API_BASE_URL = 'https://yargisalzeka-api-77794337596.europe-west1.run.app/api/v1'

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    }

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new ApiError(data.detail || 'API request failed', response.status, data)
      }

      return data
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError('Network error occurred', 0, { originalError: error.message })
    }
  }

  // GET request
  async get(endpoint, headers = {}) {
    return this.request(endpoint, {
      method: 'GET',
      headers,
    })
  }

  // POST request
  async post(endpoint, data = {}, headers = {}) {
    return this.request(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })
  }

  // PUT request
  async put(endpoint, data = {}, headers = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    })
  }

  // DELETE request
  async delete(endpoint, headers = {}) {
    return this.request(endpoint, {
      method: 'DELETE',
      headers,
    })
  }

  // Auth methods
  async login(email, password) {
    return this.post('/auth/login', { email, password })
  }

  async register(email, password, full_name) {
    return this.post('/auth/register', { email, password, full_name })
  }

  // AI methods
  async extractKeywords(caseText, headers = {}) {
    return this.post('/ai/extract-keywords', { case_text: caseText }, headers)
  }

  async smartSearch(caseText, maxResults = 10, headers = {}) {
    return this.post('/ai/smart-search', { 
      case_text: caseText, 
      max_results: maxResults 
    }, headers)
  }

  async analyzeDecision(decisionText, headers = {}) {
    return this.post('/ai/analyze-decision', { decision_text: decisionText }, headers)
  }

  // User methods
  async getUserUsage(headers = {}) {
    return this.get('/user/usage', headers)
  }

  // Workflow methods
  async generatePetition(caseText, petitionType, headers = {}) {
    return this.post('/workflow/generate-petition', {
      case_text: caseText,
      petition_type: petitionType
    }, headers)
  }

  // Health check
  async healthCheck() {
    return this.get('/health')
  }

  async detailedHealthCheck() {
    return this.get('/health/detailed')
  }
}

// Custom API Error class
class ApiError extends Error {
  constructor(message, status, data = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }

  // Check if error is due to authentication
  isAuthError() {
    return this.status === 401
  }

  // Check if error is due to rate limiting
  isRateLimitError() {
    return this.status === 429
  }

  // Check if error is due to usage limits
  isUsageLimitError() {
    return this.status === 429 && this.data.error_code === 'USAGE_LIMIT_EXCEEDED'
  }

  // Get user-friendly error message
  getUserMessage() {
    if (this.isAuthError()) {
      return 'Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.'
    }
    
    if (this.isRateLimitError()) {
      return 'Çok fazla istek gönderdiniz. Lütfen biraz bekleyin.'
    }

    if (this.isUsageLimitError()) {
      return this.data.reason || 'Kullanım limitiniz dolmuş.'
    }

    // Return the original message for other errors
    return this.message || 'Bir hata oluştu. Lütfen tekrar deneyin.'
  }
}

// Create and export API service instance
const apiService = new ApiService()

export { apiService, ApiError }
export default apiService

