<script setup>
import { ref } from 'vue';
import DisclaimerModal from './components/DisclaimerModal.vue';
import EvaluationForm from './components/EvaluationForm.vue';
import ResultDisplay from './components/ResultDisplay.vue';
import api from './services/api.js';
const isDisclaimerAgreed = ref(false);
const evaluationResult = ref(null);
const isLoading = ref(false);
const errorMessage = ref('');
const handleAgree = () => {
  isDisclaimerAgreed.value = true;
};
const handleCalculate = async (formData) => {
  isLoading.value = true;
  errorMessage.value = '';
  evaluationResult.value = null;
  try {
    const response = await api.evaluateStock(formData);
    evaluationResult.value = response.data;
  } catch (error) {
    errorMessage.value = '計算中にエラーが発生しました。入力内容を確認するか、時間をおいて再度お試しください。';
    console.error(error);
  } finally {
    isLoading.value = false;
  }
};
</script>
<template>
  <div>
    <h1>非上場株式評価シミュレーター</h1>
    <DisclaimerModal v-if="!isDisclaimerAgreed" @agree="handleAgree" />
    <div v-else>
      <EvaluationForm @calculate="handleCalculate" :is-loading="isLoading" />
      <div v-if="isLoading" class="loading">
        計算中...
      </div>
      <div v-if="errorMessage" class="error">
        {{ errorMessage }}
      </div>
      <ResultDisplay v-if="evaluationResult" :result="evaluationResult" />
    </div>
  </div>
</template>
<style scoped>
.loading, .error {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
}
.loading {
  background-color: #e9ecef;
}
.error {
  background-color: #f8d7da;
  color: #721c24;
}
</style>
