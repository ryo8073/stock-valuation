<script setup>
import { computed } from 'vue';

const props = defineProps(['result']);

const formatCurrency = (value) => {
  if (typeof value !== 'number' || isNaN(value)) return '---';
  return `${Math.round(value).toLocaleString()} 円`;
};

const hasPrincipleDetails = computed(() => {
  return props.result && props.result.details && props.result.details.comparable_value !== undefined;
});
</script>

<template>
  <div class="result-container" v-if="result">
    <h2>計算結果</h2>
    
    <div class="result-main">
      <p>1株あたりの評価額（シミュレーション）:</p>
      <h3 class="final-value">{{ formatCurrency(result.value_per_share) }}</h3>
    </div>
    
    <div class="result-details">
      <h3>評価の前提</h3>
      <p><strong>適用された評価方式:</strong> {{ result.evaluation_method || '---' }}</p>
      
      <div v-if="result.details">
        <p v-if="result.details.company_size">
          <strong>会社規模の判定:</strong> {{ result.details.company_size }}
        </p>
        <p v-if="result.details.note" class="note">
          <strong>注記:</strong> {{ result.details.note }}
        </p>
        
        <div v-if="hasPrincipleDetails" class="details-grid">
          <hr>
          <h4>参考価額</h4>
          <div class="detail-item">
            <span>類似業種比準価額:</span>
            <strong>{{ formatCurrency(result.details.comparable_value) }}</strong>
          </div>
          <div class="detail-item">
            <span>純資産価額:</span>
            <strong>{{ formatCurrency(result.details.net_asset_value) }}</strong>
          </div>
          <div v-if="result.details.combined_value" class="detail-item">
            <span>併用方式による価額:</span>
            <strong>{{ formatCurrency(result.details.combined_value) }}</strong>
          </div>
        </div>
      </div>
    </div>
    
    <div class="final-disclaimer">
      <h4>【重要】</h4>
      <p>
        本結果はシミュレーション上の概算値です。実際の評価にあたっては、必ず税理士等の専門家にご相談ください。
      </p>
    </div>
  </div>
</template>

<style scoped>
.result-container {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background-color: #f8f9fa;
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

.result-main {
  text-align: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: white;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.final-value {
  font-size: 2.5rem;
  color: var(--primary-color);
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.result-details {
  margin-bottom: 2rem;
}

.result-details h3 {
  color: var(--secondary-color);
  border-bottom: 2px solid var(--secondary-color);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.result-details hr {
  border: 0;
  border-top: 1px solid #dee2e6;
  margin: 1.5rem 0;
}

.details-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.details-grid h4 {
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 4px;
  background-color: white;
  border: 1px solid #e9ecef;
}

.detail-item:nth-child(odd) {
  background-color: #f8f9fa;
}

.detail-item span {
  font-weight: 500;
  color: #495057;
}

.detail-item strong {
  color: var(--primary-color);
  font-size: 1.1rem;
}

.note {
  font-style: italic;
  color: #555;
  background-color: #fffbe6;
  padding: 0.75rem;
  border-radius: 4px;
  border-left: 4px solid #f0ad4e;
  margin: 1rem 0;
}

.final-disclaimer {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #fff3cd;
  border-left: 5px solid #ffc107;
  border-radius: 4px;
}

.final-disclaimer h4 {
  margin-top: 0;
  color: #856404;
  font-size: 1.1rem;
}

.final-disclaimer p {
  margin-bottom: 0;
  color: #856404;
  line-height: 1.5;
}
</style>
