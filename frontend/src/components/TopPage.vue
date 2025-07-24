<template>
  <div class="page-container">
    <header class="app-header">
      <h1>Stock Valuator Pro</h1>
    </header>
    <main class="hero-section">
      <h2>複雑な非上場株評価を、シンプルに。</h2>
      <p>ガイドに従うだけで、あなたの会社の株価が分かります。</p>
      <button @click="$emit('start')" class="start-button">無料で評価を始める</button>
    </main>
    <section class="features">
        <div class="feature">✅<br>簡単操作</div>
        <div class="feature">🔢<br>高精度な計算</div>
        <div class="feature">👨‍⚖️<br>専門家監修</div>
    </section>
  </div>
</template>
