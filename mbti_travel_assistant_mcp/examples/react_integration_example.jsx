/**
 * React Integration Example for MBTI Travel Assistant MCP
 * 
 * This example demonstrates how to integrate the MBTI Travel Assistant
 * into a React application with proper state management, error handling,
 * and user experience patterns.
 */

import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import axios from 'axios';

// API Client Context
const APIClientContext = createContext(null);

// API Client Provider Component
export function APIClientProvider({ children, baseURL, authTokenProvider }) {
  const client = React.useMemo(() => {
    const axiosInstance = axios.create({
      baseURL: baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MBTITravelApp-React/1.0.0'
      }
    });
    
    // Add auth interceptor
    axiosInstance.interceptors.request.use(async (config) => {
      try {
        const token = await authTokenProvider();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Auth token error:', error);
      }
      return config;
    });
    
    return axiosInstance;
  }, [baseURL, authTokenProvider]);
  
  return (
    <APIClientContext.Provider value={client}>
      {children}
    </APIClientContext.Provider>
  );
}

// Hook to use API client
export function useAPIClient() {
  const client = useContext(APIClientContext);
  if (!client) {
    throw new Error('useAPIClient must be used within APIClientProvider');
  }
  return client;
}

// Custom hook for restaurant recommendations
export function useRestaurantRecommendation() {
  const client = useAPIClient();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchRecommendation = useCallback(async (request) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await client.post('/invocations', request);
      setData(response.data);
    } catch (err) {
      const errorInfo = err.response?.data?.error || {
        message: err.message,
        error_type: 'network_error',
        error_code: 'NETWORK_ERROR'
      };
      setError(errorInfo);
    } finally {
      setLoading(false);
    }
  }, [client]);
  
  const clearResults = useCallback(() => {
    setData(null);
    setError(null);
  }, []);
  
  return { data, loading, error, fetchRecommendation, clearResults };
}

// Search Form Component
function RestaurantSearchForm({ onSearch, loading }) {
  const [formData, setFormData] = useState({
    district: '',
    meal_time: '',
    natural_language_query: ''
  });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Build request object
    const request = {};
    if (formData.district) request.district = formData.district;
    if (formData.meal_time) request.meal_time = formData.meal_time;
    if (formData.natural_language_query) {
      request.natural_language_query = formData.natural_language_query;
    }
    
    // Validate that we have at least one search parameter
    if (!request.district && !request.natural_language_query) {
      alert('Please provide either a district or natural language query');
      return;
    }
    
    onSearch(request);
  };
  
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-section">
        <h3>Search by District & Meal Time</h3>
        
        <div className="form-group">
          <label htmlFor="district">District:</label>
          <select
            id="district"
            value={formData.district}
            onChange={(e) => handleInputChange('district', e.target.value)}
            className="form-control"
          >
            <option value="">Select District</option>
            <option value="Central district">Central</option>
            <option value="Admiralty">Admiralty</option>
            <option value="Causeway Bay">Causeway Bay</option>
            <option value="Tsim Sha Tsui">Tsim Sha Tsui</option>
            <option value="Wan Chai">Wan Chai</option>
            <option value="Mong Kok">Mong Kok</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="meal_time">Meal Time:</label>
          <select
            id="meal_time"
            value={formData.meal_time}
            onChange={(e) => handleInputChange('meal_time', e.target.value)}
            className="form-control"
          >
            <option value="">Any Time</option>
            <option value="breakfast">Breakfast</option>
            <option value="lunch">Lunch</option>
            <option value="dinner">Dinner</option>
          </select>
        </div>
      </div>
      
      <div className="form-section">
        <h3>Or Search with Natural Language</h3>
        
        <div className="form-group">
          <label htmlFor="query">Describe what you're looking for:</label>
          <input
            type="text"
            id="query"
            value={formData.natural_language_query}
            onChange={(e) => handleInputChange('natural_language_query', e.target.value)}
            placeholder="e.g., Find me a good Italian restaurant for dinner in Central"
            className="form-control"
          />
        </div>
      </div>
      
      <button 
        type="submit" 
        disabled={loading}
        className={`search-button ${loading ? 'loading' : ''}`}
      >
        {loading ? 'Searching...' : 'Find Restaurants'}
      </button>
    </form>
  );
}

// Error Display Component
function ErrorDisplay({ error, onRetry }) {
  if (!error) return null;
  
  const getErrorIcon = (errorType) => {
    switch (errorType) {
      case 'authentication_error': return '🔒';
      case 'validation_error': return '⚠️';
      case 'network_error': return '🌐';
      case 'rate_limit_error': return '⏱️';
      default: return '❌';
    }
  };
  
  return (
    <div className="error-display">
      <div className="error-header">
        <span className="error-icon">{getErrorIcon(error.error_type)}</span>
        <h3>Error: {error.error_type?.replace('_', ' ') || 'Unknown Error'}</h3>
      </div>
      
      <p className="error-message">{error.message}</p>
      
      {error.suggested_actions && error.suggested_actions.length > 0 && (
        <div className="suggested-actions">
          <h4>Suggested Actions:</h4>
          <ul>
            {error.suggested_actions.map((action, index) => (
              <li key={index}>{action}</li>
            ))}
          </ul>
        </div>
      )}
      
      {onRetry && (
        <button onClick={onRetry} className="retry-button">
          Try Again
        </button>
      )}
    </div>
  );
}

// Restaurant Card Component
function RestaurantCard({ restaurant, isRecommended = false }) {
  const formatOperatingHours = (hours) => {
    const today = new Date().toLocaleLowerCase().slice(0, 3);
    const todayHours = hours[today] || hours[Object.keys(hours)[0]];
    
    return todayHours ? todayHours.join(', ') : 'Hours not available';
  };
  
  const getSentimentColor = (percentage) => {
    if (percentage >= 80) return '#4CAF50'; // Green
    if (percentage >= 60) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };
  
  return (
    <div className={`restaurant-card ${isRecommended ? 'recommended' : ''}`}>
      {isRecommended && (
        <div className="recommended-badge">
          ⭐ Recommended
        </div>
      )}
      
      <div className="restaurant-header">
        <h3 className="restaurant-name">{restaurant.name}</h3>
        <span className="price-range">{restaurant.price_range}</span>
      </div>
      
      <div className="restaurant-details">
        <p className="address">📍 {restaurant.address}</p>
        <p className="district">🏙️ {restaurant.district}</p>
        
        <div className="meal-types">
          {restaurant.meal_type.map(type => (
            <span key={type} className="meal-type-tag">
              {type}
            </span>
          ))}
        </div>
        
        <div className="sentiment-section">
          <div className="sentiment-bar">
            <div 
              className="sentiment-fill"
              style={{ 
                width: `${restaurant.sentiment.positive_percentage}%`,
                backgroundColor: getSentimentColor(restaurant.sentiment.positive_percentage)
              }}
            />
          </div>
          <p className="sentiment-text">
            {restaurant.sentiment.positive_percentage.toFixed(1)}% positive
            ({restaurant.sentiment.total_responses} reviews)
          </p>
        </div>
        
        <div className="operating-hours">
          <p>🕒 Today: {formatOperatingHours(restaurant.operating_hours)}</p>
        </div>
        
        {restaurant.metadata && (
          <div className="additional-info">
            {restaurant.metadata.cuisine_type && (
              <p>🍽️ Cuisine: {restaurant.metadata.cuisine_type}</p>
            )}
            {restaurant.metadata.rating && (
              <p>⭐ Rating: {restaurant.metadata.rating}/5</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Results Display Component
function ResultsDisplay({ data, onClearResults }) {
  if (!data) return null;
  
  return (
    <div className="results-display">
      <div className="results-header">
        <h2>Restaurant Recommendations</h2>
        <button onClick={onClearResults} className="clear-button">
          Clear Results
        </button>
      </div>
      
      {data.recommendation && (
        <div className="recommendation-section">
          <h3>Our Top Recommendation</h3>
          <RestaurantCard restaurant={data.recommendation} isRecommended={true} />
        </div>
      )}
      
      {data.candidates && data.candidates.length > 0 && (
        <div className="candidates-section">
          <h3>Other Great Options ({data.candidates.length})</h3>
          <div className="restaurant-grid">
            {data.candidates.map(restaurant => (
              <RestaurantCard 
                key={restaurant.id} 
                restaurant={restaurant} 
                isRecommended={false} 
              />
            ))}
          </div>
        </div>
      )}
      
      {data.metadata && (
        <div className="metadata-section">
          <div className="metadata-stats">
            <div className="stat">
              <span className="stat-label">Total Found:</span>
              <span className="stat-value">{data.metadata.total_found}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Processing Time:</span>
              <span className="stat-value">{data.metadata.processing_time_ms}ms</span>
            </div>
            {data.metadata.cache_hit && (
              <div className="stat">
                <span className="stat-label">Source:</span>
                <span className="stat-value">✓ Cache</span>
              </div>
            )}
          </div>
          
          {data.metadata.search_criteria && (
            <div className="search-criteria">
              <h4>Search Criteria:</h4>
              <ul>
                {Object.entries(data.metadata.search_criteria).map(([key, value]) => (
                  <li key={key}>
                    <strong>{key.replace('_', ' ')}:</strong> {value}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Main Restaurant Recommendations Component
export function RestaurantRecommendations() {
  const { data, loading, error, fetchRecommendation, clearResults } = useRestaurantRecommendation();
  const [lastRequest, setLastRequest] = useState(null);
  
  const handleSearch = useCallback((request) => {
    setLastRequest(request);
    fetchRecommendation(request);
  }, [fetchRecommendation]);
  
  const handleRetry = useCallback(() => {
    if (lastRequest) {
      fetchRecommendation(lastRequest);
    }
  }, [lastRequest, fetchRecommendation]);
  
  return (
    <div className="restaurant-recommendations">
      <div className="app-header">
        <h1>🍽️ MBTI Travel Assistant</h1>
        <p>Discover the perfect restaurant for your taste and location</p>
      </div>
      
      <RestaurantSearchForm onSearch={handleSearch} loading={loading} />
      
      {loading && (
        <div className="loading-display">
          <div className="loading-spinner"></div>
          <p>Finding the perfect restaurants for you...</p>
        </div>
      )}
      
      <ErrorDisplay error={error} onRetry={handleRetry} />
      
      <ResultsDisplay data={data} onClearResults={clearResults} />
    </div>
  );
}

// Example App Component
export function App() {
  // Mock auth token provider - replace with your actual implementation
  const getAuthToken = useCallback(async () => {
    // In a real app, this would handle token refresh, storage, etc.
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      throw new Error('No authentication token available');
    }
    return token;
  }, []);
  
  return (
    <APIClientProvider 
      baseURL={process.env.REACT_APP_API_BASE_URL || 'https://your-endpoint.amazonaws.com'}
      authTokenProvider={getAuthToken}
    >
      <div className="App">
        <RestaurantRecommendations />
      </div>
    </APIClientProvider>
  );
}

// CSS Styles (would typically be in a separate .css file)
const styles = `
.restaurant-recommendations {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-header {
  text-align: center;
  margin-bottom: 30px;
}

.app-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.search-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-section {
  margin-bottom: 20px;
}

.form-section h3 {
  color: #495057;
  margin-bottom: 15px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.search-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #0056b3;
}

.search-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.loading-display {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-display {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.error-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.error-icon {
  font-size: 24px;
  margin-right: 10px;
}

.restaurant-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.restaurant-card.recommended {
  border-color: #28a745;
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2);
}

.recommended-badge {
  background: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 10px;
  display: inline-block;
}

.restaurant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.restaurant-name {
  margin: 0;
  color: #2c3e50;
}

.price-range {
  font-weight: bold;
  color: #28a745;
}

.meal-type-tag {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  margin-right: 5px;
}

.sentiment-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.sentiment-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.restaurant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.metadata-section {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}

.metadata-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: #6c757d;
}

.stat-value {
  font-weight: bold;
  color: #495057;
}
`;

// Inject styles (in a real app, you'd use CSS modules or styled-components)
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}

export default App;