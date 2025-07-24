<script setup>
import { ref } from 'vue';
const emit = defineEmits(['agree']);
const isAgreed = ref(false);
const proceed = () => {
  if (isAgreed.value) {
    emit('agree');
  } else {
    alert('利用規約と免責事項に同意してください。');
  }
};
</script>
<template>
  <div class="modal-overlay">
    <div class="modal-content">
      <h2>ご利用の前に</h2>
      <p>
        本シミュレーションの結果は、入力された情報に基づく概算値です。実際の評価額や税額を保証するものではありません。
      </p>
      <p>
        個別の税務相談や申告については、必ず税理士等の専門家にご相談ください。本アプリケーションの利用により生じたいかなる損害についても、開発者および提供者は一切の責任を負いません。
      </p>
      <div>
        <input type="checkbox" id="agreement" v-model="isAgreed">
        <label for="agreement">上記の利用規約および免責事項に同意します。</label>
      </div>
      <button @click="proceed" class="btn btn-primary">同意して進む</button>
    </div>
  </div>
</template>
