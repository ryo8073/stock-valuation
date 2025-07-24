import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import api from '../services/api.js'

// Mock axios
vi.mock('axios')

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('evaluateStock makes correct API call', async () => {
    const mockResponse = {
      data: {
        evaluation_method: '純資産価額方式',
        value_per_share: 500000,
        details: {
          company_size: '小会社'
        }
      }
    }

    axios.post.mockResolvedValue(mockResponse)

    const formData = {
      shares_outstanding: 1000,
      is_family_shareholder: true
    }

    const result = await api.evaluateStock(formData)

    expect(axios.post).toHaveBeenCalledWith('/api/evaluate', formData)
    expect(result).toEqual(mockResponse)
  })

  it('handles API errors correctly', async () => {
    const mockError = new Error('Network error')
    axios.post.mockRejectedValue(mockError)

    const formData = {
      shares_outstanding: 1000
    }

    await expect(api.evaluateStock(formData)).rejects.toThrow('Network error')
  })

  it('sends correct data format', async () => {
    const mockResponse = { data: {} }
    axios.post.mockResolvedValue(mockResponse)

    const formData = {
      shares_outstanding: 1000,
      company_size: {
        employees: 50,
        assets: 500000000,
        sales: 1000000000
      },
      net_asset: {
        assets: 1000000000,
        liabilities: 500000000,
        unrealized_gains: 200000000
      }
    }

    await api.evaluateStock(formData)

    expect(axios.post).toHaveBeenCalledWith('/api/evaluate', formData)
  })

  it('handles empty response', async () => {
    const mockResponse = { data: null }
    axios.post.mockResolvedValue(mockResponse)

    const result = await api.evaluateStock({})

    expect(result.data).toBeNull()
  })

  it('handles malformed response', async () => {
    const mockResponse = { data: { invalid: 'data' } }
    axios.post.mockResolvedValue(mockResponse)

    const result = await api.evaluateStock({})

    expect(result.data).toEqual({ invalid: 'data' })
  })
}) 