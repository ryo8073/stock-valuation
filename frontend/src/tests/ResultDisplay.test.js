import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ResultDisplay from '../components/ResultDisplay.vue'

describe('ResultDisplay', () => {
  let wrapper

  const mockResult = {
    evaluation_method: '純資産価額方式',
    value_per_share: 500000,
    details: {
      company_size: '小会社',
      net_asset_value: 500000,
      comparable_value: 600000,
      note: 'テスト用の注記'
    }
  }

  beforeEach(() => {
    wrapper = mount(ResultDisplay, {
      props: {
        result: mockResult
      }
    })
  })

  it('renders properly', () => {
    expect(wrapper.find('.result-container').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('計算結果')
  })

  it('displays the final value correctly', () => {
    const finalValue = wrapper.find('.final-value')
    expect(finalValue.text()).toBe('500,000 円')
  })

  it('displays evaluation method', () => {
    const methodText = wrapper.text()
    expect(methodText).toContain('純資産価額方式')
  })

  it('displays company size', () => {
    const sizeText = wrapper.text()
    expect(sizeText).toContain('小会社')
  })

  it('displays reference values when available', () => {
    const detailsGrid = wrapper.find('.details-grid')
    expect(detailsGrid.exists()).toBe(true)
    
    const comparableValue = wrapper.text()
    expect(comparableValue).toContain('600,000 円')
  })

  it('displays note when available', () => {
    const noteElement = wrapper.find('.note')
    expect(noteElement.text()).toContain('テスト用の注記')
  })

  it('displays disclaimer', () => {
    const disclaimer = wrapper.find('.final-disclaimer')
    expect(disclaimer.exists()).toBe(true)
    expect(disclaimer.text()).toContain('【重要】')
  })

  it('handles missing result gracefully', () => {
    const emptyWrapper = mount(ResultDisplay, {
      props: {
        result: null
      }
    })
    
    expect(emptyWrapper.find('.result-container').exists()).toBe(false)
  })

  it('formats currency correctly', () => {
    const resultWithLargeNumber = {
      ...mockResult,
      value_per_share: 1234567
    }
    
    const largeWrapper = mount(ResultDisplay, {
      props: {
        result: resultWithLargeNumber
      }
    })
    
    const finalValue = largeWrapper.find('.final-value')
    expect(finalValue.text()).toBe('1,234,567 円')
  })

  it('handles NaN values', () => {
    const resultWithNaN = {
      ...mockResult,
      value_per_share: NaN
    }
    
    const nanWrapper = mount(ResultDisplay, {
      props: {
        result: resultWithNaN
      }
    })
    
    const finalValue = nanWrapper.find('.final-value')
    expect(finalValue.text()).toBe('---')
  })

  it('shows combined value when available', () => {
    const resultWithCombined = {
      ...mockResult,
      details: {
        ...mockResult.details,
        combined_value: 550000
      }
    }
    
    const combinedWrapper = mount(ResultDisplay, {
      props: {
        result: resultWithCombined
      }
    })
    
    const combinedText = combinedWrapper.text()
    expect(combinedText).toContain('550,000 円')
  })
}) 