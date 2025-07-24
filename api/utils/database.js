// api/utils/database.js
import { Pool } from 'pg';

export async function updateDatabase(data) {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });
  
  try {
    // トランザクション開始
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // 1. 類似業種データの更新
      if (data.comparable) {
        await updateComparableData(client, data.comparable);
      }
      
      // 2. 配当還元率データの更新
      if (data.dividend) {
        await updateDividendData(client, data.dividend);
      }
      
      // 3. 会社規模判定基準データの更新
      if (data.company_size) {
        await updateCompanySizeData(client, data.company_size);
      }
      
      // 4. 更新履歴の記録
      await recordUpdateHistory(client, data);
      
      await client.query('COMMIT');
      console.log('Database update completed successfully');
      
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
    
  } finally {
    await pool.end();
  }
}

async function updateComparableData(client, comparableData) {
  // 既存データを削除
  await client.query('DELETE FROM comparable_industry_data');
  
  // 新しいデータを挿入
  for (const industry of comparableData.industries) {
    await client.query(`
      INSERT INTO comparable_industry_data 
      (industry_code, industry_name, average_price, average_dividend, average_profit, average_net_assets, created_at)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `, [
      industry.industry_code,
      industry.industry_name,
      industry.average_price || null,
      industry.average_dividend || null,
      industry.average_profit || null,
      industry.average_net_assets || null
    ]);
  }
  
  console.log(`Updated ${comparableData.industries.length} comparable industry records`);
}

async function updateDividendData(client, dividendData) {
  // 既存データを削除
  await client.query('DELETE FROM dividend_reduction_rates');
  
  // 新しいデータを挿入
  for (const rate of dividendData.rates) {
    await client.query(`
      INSERT INTO dividend_reduction_rates 
      (capital_range_min, capital_range_max, reduction_rate, created_at)
      VALUES ($1, $2, $3, NOW())
    `, [
      rate.capital_range_min,
      rate.capital_range_max,
      rate.reduction_rate
    ]);
  }
  
  console.log(`Updated ${dividendData.rates.length} dividend reduction rate records`);
}

async function updateCompanySizeData(client, companySizeData) {
  // 既存データを削除
  await client.query('DELETE FROM company_size_criteria');
  
  // 新しいデータを挿入
  for (const criterion of companySizeData.criteria) {
    await client.query(`
      INSERT INTO company_size_criteria 
      (industry_type, size_category, employee_min, employee_max, asset_min, asset_max, sales_min, sales_max, created_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
    `, [
      criterion.industry_type,
      criterion.size_category,
      criterion.employee_min || null,
      criterion.employee_max || null,
      criterion.asset_min || null,
      criterion.asset_max || null,
      criterion.sales_min || null,
      criterion.sales_max || null
    ]);
  }
  
  console.log(`Updated ${companySizeData.criteria.length} company size criteria records`);
}

async function recordUpdateHistory(client, data) {
  await client.query(`
    INSERT INTO update_history 
    (data_type, update_status, record_count, fetched_at, created_at)
    VALUES ($1, $2, $3, $4, NOW())
  `, [
    'full_update',
    'completed',
    calculateTotalRecords(data),
    data.fetched_at
  ]);
}

function calculateTotalRecords(data) {
  let total = 0;
  
  if (data.comparable && data.comparable.industries) {
    total += data.comparable.industries.length;
  }
  
  if (data.dividend && data.dividend.rates) {
    total += data.dividend.rates.length;
  }
  
  if (data.company_size && data.company_size.criteria) {
    total += data.company_size.criteria.length;
  }
  
  return total;
}

// データベース初期化関数
export async function initializeDatabase() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });
  
  try {
    const client = await pool.connect();
    
    try {
      // 類似業種比準価額データテーブル
      await client.query(`
        CREATE TABLE IF NOT EXISTS comparable_industry_data (
          id SERIAL PRIMARY KEY,
          industry_code VARCHAR(10) NOT NULL,
          industry_name VARCHAR(200) NOT NULL,
          average_price DECIMAL(10,2),
          average_dividend DECIMAL(5,2),
          average_profit DECIMAL(10,2),
          average_net_assets DECIMAL(10,2),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // 配当還元率データテーブル
      await client.query(`
        CREATE TABLE IF NOT EXISTS dividend_reduction_rates (
          id SERIAL PRIMARY KEY,
          capital_range_min INTEGER NOT NULL,
          capital_range_max INTEGER NOT NULL,
          reduction_rate DECIMAL(5,4) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // 会社規模判定基準テーブル
      await client.query(`
        CREATE TABLE IF NOT EXISTS company_size_criteria (
          id SERIAL PRIMARY KEY,
          industry_type VARCHAR(50) NOT NULL,
          size_category VARCHAR(20) NOT NULL,
          employee_min INTEGER,
          employee_max INTEGER,
          asset_min INTEGER,
          asset_max INTEGER,
          sales_min INTEGER,
          sales_max INTEGER,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // 更新履歴テーブル
      await client.query(`
        CREATE TABLE IF NOT EXISTS update_history (
          id SERIAL PRIMARY KEY,
          data_type VARCHAR(50) NOT NULL,
          update_status VARCHAR(20) NOT NULL,
          record_count INTEGER,
          fetched_at TIMESTAMP,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      console.log('Database tables initialized successfully');
      
    } finally {
      client.release();
    }
    
  } finally {
    await pool.end();
  }
} 