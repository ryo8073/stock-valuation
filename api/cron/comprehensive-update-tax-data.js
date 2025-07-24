const { ComprehensiveNTAScraper } = require('../utils/comprehensive-nta-scraper');

/**
 * 包括的国税庁データ自動更新Cronジョブ
 * 定期データ、業種目別データ、一部改正通達を網羅的に更新
 */

export default async function handler(req, res) {
  // Vercel Cron Jobsからの呼び出しを確認
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const authHeader = req.headers.authorization;
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const startTime = Date.now();
  const scraper = new ComprehensiveNTAScraper();

  try {
    console.log('🚀 包括的国税庁データ自動更新を開始...');
    
    // 包括的なデータ更新を実行
    const result = await scraper.comprehensiveUpdate();
    
    const duration = Date.now() - startTime;
    
    console.log(`✅ 包括的データ更新完了: ${duration}ms`);
    console.log(`📊 更新結果:`, result.updateResults);
    
    return res.status(200).json({
      success: true,
      message: '包括的データ更新が完了しました',
      duration,
      results: result.updateResults
    });
    
  } catch (error) {
    console.error('❌ 包括的データ更新に失敗:', error);
    
    const duration = Date.now() - startTime;
    
    return res.status(500).json({
      success: false,
      error: error.message,
      duration
    });
  }
} 