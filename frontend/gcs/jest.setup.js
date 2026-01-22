import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => require('next-router-mock'))

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url
    this.readyState = 1
  }
  
  send() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
}

// Mock fetch
global.fetch = jest.fn()