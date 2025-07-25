// api/cron/update-tax-data.js
import { fetchNTAData, validateData, updateDatabase } from '../utils';

export default async function handler(req, res) {
  // Cron jobからの実行のみ許可
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    console.log('Starting scheduled tax data update...');
    
    // 1. 国税庁サイトからデータ取得
    const latestData = await fetchNTAData();
    
    // 2. データ検証
    const validationResult = await validateData(latestData);
    if (!validationResult.isValid) {
      throw new Error(`Data validation failed: ${validationResult.errors.join(', ')}`);
    }
    
    // 3. 現在のデータと比較
    const currentData = await getCurrentData();
    const hasChanges = compareData(latestData, currentData);
    
    if (hasChanges) {
      // 4. データベース更新
      await updateDatabase(latestData);
      
      console.log('Tax data update completed successfully');
      res.status(200).json({ 
        status: 'success', 
        message: 'Data updated',
        changes: hasChanges.length 
      });
    } else {
      console.log('No changes detected in tax data');
      res.status(200).json({ 
        status: 'success', 
        message: 'No changes detected' 
      });
    }
    
  } catch (error) {
    console.error('Tax data update failed:', error);
    
    res.status(500).json({ 
      status: 'error', 
      message: error.message 
    });
  }
}

async function getCurrentData() {
  // 現在のデータベースからデータを取得
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });
  
  try {
    const result = await pool.query('SELECT * FROM tax_data ORDER BY updated_at DESC LIMIT 1');
    return result.rows[0] || null;
  } finally {
    await pool.end();
  }
}

function compareData(latestData, currentData) {
  if (!currentData) return latestData;
  
  // データの変更を検出
  const changes = [];
  
  // 類似業種比準価額データの比較
  if (JSON.stringify(latestData.comparable) !== JSON.stringify(currentData.comparable)) {
    changes.push('comparable_industry_data');
  }
  
  // 配当還元率データの比較
  if (JSON.stringify(latestData.dividend) !== JSON.stringify(currentData.dividend)) {
    changes.push('dividend_reduction_rates');
  }
  
  // 会社規模判定基準データの比較
  if (JSON.stringify(latestData.company_size) !== JSON.stringify(currentData.company_size)) {
    changes.push('company_size_criteria');
  }
  
  return changes;
} 