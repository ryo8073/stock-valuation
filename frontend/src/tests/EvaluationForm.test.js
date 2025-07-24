import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import EvaluationForm from '../components/EvaluationForm.vue'

describe('EvaluationForm', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(EvaluationForm, {
      props: {
        isLoading: false
      }
    })
  })

  it('renders properly', () => {
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('1. 評価の基本条件')
  })

  it('has correct initial data', () => {
    const formData = wrapper.vm.formData
    expect(formData.shares_outstanding).toBe(1000)
    expect(formData.is_family_shareholder).toBe(true)
    expect(formData.company_size.employees).toBe(10)
  })

  it('emits calculate event when form is submitted', async () => {
    await wrapper.find('form').trigger('submit')
    
    expect(wrapper.emitted('calculate')).toBeTruthy()
    expect(wrapper.emitted('calculate')[0][0]).toHaveProperty('shares_outstanding')
  })

  it('shows principle evaluation form when principle is selected', async () => {
    await wrapper.setData({ evaluationType: 'principle' })
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('h3').text()).toContain('会社の規模等の判定要素')
  })

  it('shows dividend evaluation form when dividend is selected', async () => {
    await wrapper.setData({ evaluationType: 'dividend' })
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('h3').text()).toContain('配当還元方式の計算要素')
  })

  it('updates form data when inputs change', async () => {
    const sharesInput = wrapper.find('#shares_outstanding')
    await sharesInput.setValue(2000)
    
    expect(wrapper.vm.formData.shares_outstanding).toBe(2000)
  })

  it('disables submit button when loading', async () => {
    await wrapper.setProps({ isLoading: true })
    
    const submitButton = wrapper.find('button[type="submit"]')
    expect(submitButton.attributes('disabled')).toBeDefined()
  })

  it('shows loading text when loading', async () => {
    await wrapper.setProps({ isLoading: true })
    
    const submitButton = wrapper.find('button[type="submit"]')
    expect(submitButton.text()).toBe('計算中...')
  })
}) 