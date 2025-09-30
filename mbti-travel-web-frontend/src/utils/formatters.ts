// Formatting utility functions
export function formatOperatingHours(hours: string): string {
  if (!hours || hours.toLowerCase() === 'closed') {
    return 'Closed'
  }
  return hours
}

export function formatPriceRange(priceRange: string): string {
  if (!priceRange) {
    return 'Price not available'
  }
  return priceRange
}

export function formatSentimentScore(likes: number, dislikes: number, neutral: number): string {
  const total = likes + dislikes + neutral
  if (total === 0) {
    return 'No reviews'
  }

  const percentage = Math.round((likes / total) * 100)
  return `${percentage}% positive (${total} reviews)`
}

export function formatAddress(address: string, district?: string): string {
  if (!address) {
    return 'Address not available'
  }

  if (district && !address.includes(district)) {
    return `${address}, ${district}`
  }

  return address
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text
  }

  return text.substring(0, maxLength - 3) + '...'
}
