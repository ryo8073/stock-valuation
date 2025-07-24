#!/usr/bin/env node
/**
 * Vercel Postgres セットアップスクリプト
 * ゼロからVercel Postgresを設定し、データベーススキーマを作成
 */

const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// 環境変数の読み込み
require('dotenv').config({ path: '.env.local' });

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL が設定されていません');
  console.log('以下のコマンドでVercel Postgresを作成してください:');
  console.log('vercel storage create postgres');
  process.exit(1);
}

async function setupDatabase() {
  const pool = new Pool({
    connectionString: DATABASE_URL,
    ssl: {
      rejectUnauthorized: false
    }
  });

  try {
    console.log('🔗 データベースに接続中...');
    const client = await pool.connect();
    
    console.log('✅ データベース接続成功');
    
    // 1. 類似業種比準価額データテーブル
    console.log('📊 類似業種比準価額データテーブルを作成中...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS comparable_industry_data (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        industry_code VARCHAR(10) NOT NULL,
        industry_name VARCHAR(200) NOT NULL,
        average_price DECIMAL(10,2),
        average_dividend DECIMAL(5,2),
        average_profit DECIMAL(10,2),
        average_net_assets DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(year, month, industry_code)
      )
    `);
    
    // インデックスの作成
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_comparable_industry_code 
      ON comparable_industry_data(industry_code)
    `);
    
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_comparable_year_month 
      ON comparable_industry_data(year, month)
    `);
    
    console.log('✅ 類似業種比準価額データテーブル作成完了');

    // 2. 配当還元率データテーブル
    console.log('📊 配当還元率データテーブルを作成中...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS dividend_reduction_rates (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        capital_range_min BIGINT NOT NULL,
        capital_range_max BIGINT NOT NULL,
        reduction_rate DECIMAL(5,4) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(year, month, capital_range_min, capital_range_max)
      )
    `);
    
    // インデックスの作成
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_dividend_capital_range 
      ON dividend_reduction_rates(capital_range_min, capital_range_max)
    `);
    
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_dividend_year_month 
      ON dividend_reduction_rates(year, month)
    `);
    
    console.log('✅ 配当還元率データテーブル作成完了');

    // 3. 会社規模判定基準テーブル
    console.log('📊 会社規模判定基準テーブルを作成中...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS company_size_criteria (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        industry_type VARCHAR(50) NOT NULL,
        size_category VARCHAR(20) NOT NULL,
        employee_min BIGINT,
        employee_max BIGINT,
        asset_min BIGINT,
        asset_max BIGINT,
        sales_min BIGINT,
        sales_max BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(year, month, industry_type, size_category)
      )
    `);
    
    // インデックスの作成
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_company_size_industry 
      ON company_size_criteria(industry_type)
    `);
    
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_company_size_category 
      ON company_size_criteria(size_category)
    `);
    
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_company_size_year_month 
      ON company_size_criteria(year, month)
    `);
    
    console.log('✅ 会社規模判定基準テーブル作成完了');

    // 4. 更新履歴テーブル
    console.log('📊 更新履歴テーブルを作成中...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS update_history (
        id SERIAL PRIMARY KEY,
        check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_type VARCHAR(50) NOT NULL,
        last_modified VARCHAR(100),
        etag VARCHAR(100),
        content_hash VARCHAR(64),
        update_available BOOLEAN DEFAULT FALSE,
        update_status VARCHAR(20) DEFAULT 'pending',
        admin_approved BOOLEAN DEFAULT FALSE,
        update_executed_at TIMESTAMP,
        record_count INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // インデックスの作成
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_update_history_data_type 
      ON update_history(data_type)
    `);
    
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_update_history_check_date 
      ON update_history(check_date)
    `);
    
    console.log('✅ 更新履歴テーブル作成完了');

    // 5. システム設定テーブル
    console.log('📊 システム設定テーブルを作成中...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS system_settings (
        id SERIAL PRIMARY KEY,
        setting_key VARCHAR(100) UNIQUE NOT NULL,
        setting_value TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // デフォルト設定の挿入
    await client.query(`
      INSERT INTO system_settings (setting_key, setting_value, description) VALUES
      ('last_update_check', NULL, '最後の更新チェック日時'),
      ('update_interval_hours', '168', '更新チェック間隔（時間）'),
      ('notification_enabled', 'true', '通知機能の有効/無効'),
      ('auto_update_enabled', 'false', '自動更新の有効/無効'),
      ('data_retention_days', '365', 'データ保持期間（日）')
      ON CONFLICT (setting_key) DO NOTHING
    `);
    
    console.log('✅ システム設定テーブル作成完了');

    // 6. 更新トリガー関数の作成
    console.log('📊 更新トリガー関数を作成中...');
    await client.query(`
      CREATE OR REPLACE FUNCTION update_updated_at_column()
      RETURNS TRIGGER AS $$
      BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
      END;
      $$ language 'plpgsql';
    `);
    
    // 各テーブルにトリガーを設定
    const tables = [
      'comparable_industry_data',
      'dividend_reduction_rates', 
      'company_size_criteria',
      'system_settings'
    ];
    
    for (const table of tables) {
      await client.query(`
        DROP TRIGGER IF EXISTS update_${table}_updated_at ON ${table};
        CREATE TRIGGER update_${table}_updated_at
          BEFORE UPDATE ON ${table}
          FOR EACH ROW
          EXECUTE FUNCTION update_updated_at_column();
      `);
    }
    
    console.log('✅ 更新トリガー関数作成完了');

    // 7. サンプルデータの挿入（オプション）
    if (process.argv.includes('--with-sample-data')) {
      console.log('📊 サンプルデータを挿入中...');
      await insertSampleData(client);
      console.log('✅ サンプルデータ挿入完了');
    }

    console.log('\n🎉 データベースセットアップ完了！');
    console.log('\n📋 作成されたテーブル:');
    console.log('  - comparable_industry_data (類似業種比準価額データ)');
    console.log('  - dividend_reduction_rates (配当還元率データ)');
    console.log('  - company_size_criteria (会社規模判定基準)');
    console.log('  - update_history (更新履歴)');
    console.log('  - system_settings (システム設定)');

    client.release();
    
  } catch (error) {
    console.error('❌ データベースセットアップエラー:', error);
    throw error;
  } finally {
    await pool.end();
  }
}

async function insertSampleData(client) {
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  
  // サンプル類似業種データ
  await client.query(`
    INSERT INTO comparable_industry_data (year, month, industry_code, industry_name, average_price, average_dividend, average_profit, average_net_assets) VALUES
    (${currentYear}, ${currentMonth}, '01', '製造業', 1500.00, 2.5, 8.0, 1200.00),
    (${currentYear}, ${currentMonth}, '02', '建設業', 1200.00, 2.0, 6.5, 1000.00),
    (${currentYear}, ${currentMonth}, '03', '卸売業', 1800.00, 3.0, 10.0, 1500.00),
    (${currentYear}, ${currentMonth}, '04', '小売業', 1600.00, 2.8, 9.0, 1300.00),
    (${currentYear}, ${currentMonth}, '05', 'サービス業', 1400.00, 2.2, 7.5, 1100.00)
    ON CONFLICT (year, month, industry_code) DO NOTHING
  `);
  
  // サンプル配当還元率データ
  await client.query(`
    INSERT INTO dividend_reduction_rates (year, month, capital_range_min, capital_range_max, reduction_rate) VALUES
    (${currentYear}, ${currentMonth}, 0, 10000000, 0.0500),
    (${currentYear}, ${currentMonth}, 10000000, 50000000, 0.0400),
    (${currentYear}, ${currentMonth}, 50000000, 100000000, 0.0350),
    (${currentYear}, ${currentMonth}, 100000000, 500000000, 0.0300),
    (${currentYear}, ${currentMonth}, 500000000, 999999999, 0.0250)
    ON CONFLICT (year, month, capital_range_min, capital_range_max) DO NOTHING
  `);
  
  // サンプル会社規模判定基準データ
  await client.query(`
    INSERT INTO company_size_criteria (year, month, industry_type, size_category, employee_min, employee_max, asset_min, asset_max, sales_min, sales_max) VALUES
    (${currentYear}, ${currentMonth}, 'manufacturing', '小会社', 0, 50, 0, 100000000, 0, 200000000),
    (${currentYear}, ${currentMonth}, 'manufacturing', '中会社', 51, 300, 100000000, 1000000000, 200000000, 2000000000),
    (${currentYear}, ${currentMonth}, 'manufacturing', '大会社', 301, 999999, 1000000000, 999999999999, 2000000000, 999999999999),
    (${currentYear}, ${currentMonth}, 'wholesale', '小会社', 0, 100, 0, 50000000, 0, 100000000),
    (${currentYear}, ${currentMonth}, 'wholesale', '中会社', 101, 100, 50000000, 500000000, 100000000, 1000000000),
    (${currentYear}, ${currentMonth}, 'wholesale', '大会社', 101, 999999, 500000000, 999999999999, 1000000000, 999999999999)
    ON CONFLICT (year, month, industry_type, size_category) DO NOTHING
  `);
}

// メイン実行
if (require.main === module) {
  setupDatabase()
    .then(() => {
      console.log('\n🚀 セットアップが正常に完了しました！');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 セットアップに失敗しました:', error);
      process.exit(1);
    });
}

module.exports = { setupDatabase }; 