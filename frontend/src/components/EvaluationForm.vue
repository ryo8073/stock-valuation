<script setup>
import { ref, reactive } from 'vue';
defineProps(['isLoading']);
const emit = defineEmits(['calculate']);
const evaluationType = ref('principle'); // 'principle' or 'dividend'

// reactiveを使用して、フォームデータを構造化
const formData = reactive({
  is_family_shareholder: true,
  shares_outstanding: 1000,
  
  // 原則的評価方式で利用
  company_size: {
    employees: 10,
    assets: 50000000, // 5千万円
    sales: 100000000,  // 1億円
  },
  net_asset: {
    assets: 100000000, // 1億円
    liabilities: 50000000, // 5千万円
    unrealized_gains: 20000000, // 2千万円
  },
  comparable: {
    dividend: 15,
    profit: 100,
    net_assets: 400,
  },
  // 配当還元方式で利用
  dividend_reduction: {
    dividend1: 10,
    dividend2: 12,
    capital: 50000000, // 5千万円
  },
});

const submitForm = () => {
  formData.is_family_shareholder = (evaluationType.value === 'principle');
  // reactiveオブジェクトをプレーンなオブジェクトに変換して渡す
  emit('calculate', JSON.parse(JSON.stringify(formData)));
};
</script>

<template>
  <form @submit.prevent="submitForm" class="evaluation-form">
    <h2>1. 評価の基本条件</h2>
    <div class="form-section">
      <div class="form-group">
        <label for="evaluationType">評価方法の選択</label>
        <select id="evaluationType" v-model="evaluationType">
          <option value="principle">原則的評価方式（同族株主等）</option>
          <option value="dividend">特例的評価方式（配当還元方式）</option>
        </select>
      </div>
      <div class="form-group">
        <label for="shares_outstanding">発行済株式数</label>
        <input type="number" id="shares_outstanding" v-model.number="formData.shares_outstanding" min="1">
      </div>
    </div>
    
    <!-- 原則的評価方式の入力欄 -->
    <div v-if="evaluationType === 'principle'">
      <h2>2. 原則的評価方式の入力</h2>
      
      <div class="form-section">
        <h3>会社の規模等の判定要素</h3>
        <div class="form-group">
          <label for="employees">従業員数（人）</label>
          <input type="number" id="employees" v-model.number="formData.company_size.employees" min="0">
        </div>
        <div class="form-group">
          <label for="assets">総資産価額（帳簿価額、円）</label>
          <input type="number" id="assets" v-model.number="formData.company_size.assets" min="0">
        </div>
        <div class="form-group">
          <label for="sales">直前期末以前1年間の取引金額（円）</label>
          <input type="number" id="sales" v-model.number="formData.company_size.sales" min="0">
        </div>
      </div>
      
      <div class="form-section">
        <h3>純資産価額方式の計算要素</h3>
        <div class="form-group">
          <label>相続税評価額による総資産（円）</label>
          <input type="number" v-model.number="formData.net_asset.assets" min="0">
        </div>
        <div class="form-group">
          <label>相続税評価額による負債（円）</label>
          <input type="number" v-model.number="formData.net_asset.liabilities" min="0">
        </div>
        <div class="form-group">
          <label>資産の含み益（評価差額、円）</label>
          <input type="number" v-model.number="formData.net_asset.unrealized_gains" min="0">
        </div>
      </div>
      
      <div class="form-section">
        <h3>類似業種比準価額方式の計算要素</h3>
        <div class="form-group">
          <label>1株当たりの配当金額（円）</label>
          <input type="number" v-model.number="formData.comparable.dividend" min="0">
        </div>
        <div class="form-group">
          <label>1株当たりの利益金額（円）</label>
          <input type="number" v-model.number="formData.comparable.profit" min="0">
        </div>
        <div class="form-group">
          <label>1株当たりの純資産価額（簿価、円）</label>
          <input type="number" v-model.number="formData.comparable.net_assets" min="0">
        </div>
      </div>
    </div>
    
    <!-- 配当還元方式の入力欄 -->
    <div v-if="evaluationType === 'dividend'">
      <h2>2. 配当還元方式の入力</h2>
      <div class="form-section">
        <div class="form-group">
          <label>直前期の1株当たり年間配当金（円）</label>
          <input type="number" v-model.number="formData.dividend_reduction.dividend1" min="0">
        </div>
        <div class="form-group">
          <label>前々期の1株当たり年間配当金（円）</label>
          <input type="number" v-model.number="formData.dividend_reduction.dividend2" min="0">
        </div>
        <div class="form-group">
          <label>資本金等の額（円）</label>
          <input type="number" v-model.number="formData.dividend_reduction.capital" min="0">
        </div>
      </div>
    </div>
    
    <button type="submit" class="btn btn-primary" :disabled="isLoading">
      {{ isLoading ? '計算中...' : '評価額を計算する' }}
    </button>
  </form>
</template>

<style scoped>
.evaluation-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-section {
  padding: 1.5rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background-color: #f8f9fa;
}

h2 {
  margin-top: 0;
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
  color: var(--primary-color);
}

h3 {
  margin-top: 0;
  font-size: 1.2rem;
  color: var(--secondary-color);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  transform: none;
}
</style> 