const { parsePDF } = require('./pdf-parser');
const { validateData } = require('./data-validator');
const { saveToDatabase } = require('./database');
const { sendNotification } = require('./notification');

/**
 * 包括的国税庁データ自動取得・解析システム
 * 定期データ、業種目別データ、一部改正通達を網羅
 */

class ComprehensiveNTAScraper {
  constructor() {
    this.baseUrl = 'https://www.nta.go.jp';
    this.dataUrl = 'https://www.nta.go.jp/law/tsutatsu/kobetsu/hyoka/zaisan.htm';
    this.pdfBaseUrl = 'https://www.nta.go.jp/law/tsutatsu/kobetsu/hyoka';
    
    // データソースの定義
    this.dataSources = {
      // 年1回の定期データ
      annual: {
        pattern: /href="([^"]*r\d{2}\/\d{4}\/pdf\/[^"]*list_all\.pdf)"/g,
        type: 'annual_comparable',
        frequency: 'yearly'
      },
      // 2ヶ月ごとの業種目別データ
      bimonthly: {
        pattern: /href="([^"]*\d{6}\/pdf\/\d{2}_\d{2}\/list_all\.pdf)"/g,
        type: 'bimonthly_detailed',
        frequency: 'bimonthly'
      },
      // 一部改正通達
      amendments: {
        pattern: /href="([^"]*kaisei\/[^"]*\.htm)"/g,
        type: 'amendment_notice',
        frequency: 'irregular'
      }
    };
  }

  /**
   * 国税庁サイトから全データソースの情報を取得
   */
  async getAllDataSources() {
    try {
      console.log('🔍 国税庁サイトから全データソース情報を取得中...');
      
      const response = await fetch(this.dataUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const html = await response.text();
      const sources = {};
      
      // 各データソースタイプを検索
      for (const [key, config] of Object.entries(this.dataSources)) {
        const matches = [];
        let match;
        
        while ((match = config.pattern.exec(html)) !== null) {
          const url = this.baseUrl + match[1];
          const metadata = this.extractMetadataFromUrl(url, config.type);
          
          matches.push({
            url,
            type: config.type,
            frequency: config.frequency,
            ...metadata
          });
        }
        
        sources[key] = matches;
      }
      
      console.log(`✅ データソース検索完了:`);
      console.log(`  定期データ: ${sources.annual.length}件`);
      console.log(`  業種目別データ: ${sources.bimonthly.length}件`);
      console.log(`  一部改正通達: ${sources.amendments.length}件`);
      
      return sources;
      
    } catch (error) {
      console.error('❌ データソース情報の取得に失敗:', error);
      throw error;
    }
  }

  /**
   * URLからメタデータを抽出
   */
  extractMetadataFromUrl(url, type) {
    const metadata = { url, type };
    
    try {
      switch (type) {
        case 'annual_comparable':
          // r07/2506/pdf/01-12/list_all.pdf
          const annualMatch = url.match(/r(\d{2})\/(\d{4})\/pdf/);
          if (annualMatch) {
            metadata.year = parseInt('20' + annualMatch[1]);
            metadata.month = parseInt(annualMatch[2].substring(0, 2));
            metadata.period = 'annual';
          }
          break;
          
        case 'bimonthly_detailed':
          // 250600/pdf/03_04/list_all.pdf
          const bimonthlyMatch = url.match(/(\d{6})\/pdf\/(\d{2})_(\d{2})/);
          if (bimonthlyMatch) {
            const yearMonth = bimonthlyMatch[1];
            metadata.year = parseInt('20' + yearMonth.substring(0, 2));
            metadata.month = parseInt(yearMonth.substring(2, 4));
            metadata.period = 'bimonthly';
            metadata.periodNumber = parseInt(bimonthlyMatch[2]);
            metadata.subPeriod = parseInt(bimonthlyMatch[3]);
          }
          break;
          
        case 'amendment_notice':
          // kaisei/kaisei36.htm
          const amendmentMatch = url.match(/kaisei(\d+)\.htm/);
          if (amendmentMatch) {
            metadata.amendmentNumber = parseInt(amendmentMatch[1]);
            metadata.period = 'amendment';
          }
          break;
      }
    } catch (error) {
      console.warn(`⚠️ URLメタデータ抽出エラー: ${url}`, error);
    }
    
    return metadata;
  }

  /**
   * 最新データの優先順位を決定
   */
  prioritizeDataSources(sources) {
    const prioritized = [];
    
    // 1. 最新の定期データを最優先
    if (sources.annual.length > 0) {
      const latestAnnual = sources.annual.sort((a, b) => 
        (b.year * 100 + b.month) - (a.year * 100 + a.month)
      )[0];
      prioritized.push({ ...latestAnnual, priority: 1 });
    }
    
    // 2. 最新の業種目別データ
    if (sources.bimonthly.length > 0) {
      const latestBimonthly = sources.bimonthly.sort((a, b) => 
        (b.year * 100 + b.month) - (a.year * 100 + a.month)
      )[0];
      prioritized.push({ ...latestBimonthly, priority: 2 });
    }
    
    // 3. 最新の一部改正通達
    if (sources.amendments.length > 0) {
      const latestAmendment = sources.amendments.sort((a, b) => 
        (b.amendmentNumber || 0) - (a.amendmentNumber || 0)
      )[0];
      prioritized.push({ ...latestAmendment, priority: 3 });
    }
    
    return prioritized;
  }

  /**
   * データの更新必要性をチェック
   */
  async checkUpdateNecessity(prioritizedSources) {
    try {
      console.log('🔍 データ更新必要性をチェック中...');
      
      const updateChecks = [];
      
      for (const source of prioritizedSources) {
        const existingData = await this.getExistingData(source.type, source.year, source.month);
        const needsUpdate = this.needsUpdate(source, existingData);
        
        updateChecks.push({
          source,
          existingData,
          needsUpdate,
          reason: this.getUpdateReason(source, existingData)
        });
      }
      
      return updateChecks;
      
    } catch (error) {
      console.error('❌ 更新必要性チェックに失敗:', error);
      throw error;
    }
  }

  /**
   * 既存データを取得
   */
  async getExistingData(type, year, month) {
    try {
      const { Pool } = require('pg');
      const pool = new Pool({ connectionString: process.env.DATABASE_URL });
      
      let query;
      let params;
      
      switch (type) {
        case 'annual_comparable':
          query = 'SELECT * FROM comparable_industry_data WHERE year = $1 AND month = $2';
          params = [year, month];
          break;
        case 'bimonthly_detailed':
          query = 'SELECT * FROM comparable_industry_data WHERE year = $1 AND month = $2 AND data_type = $3';
          params = [year, month, 'bimonthly'];
          break;
        case 'amendment_notice':
          query = 'SELECT * FROM update_history WHERE data_type = $1 ORDER BY check_date DESC LIMIT 1';
          params = ['amendment'];
          break;
        default:
          return null;
      }
      
      const result = await pool.query(query, params);
      await pool.end();
      
      return result.rows;
      
    } catch (error) {
      console.error('❌ 既存データ取得に失敗:', error);
      return null;
    }
  }

  /**
   * 更新必要性を判定
   */
  needsUpdate(source, existingData) {
    if (!existingData || existingData.length === 0) {
      return true; // データが存在しない場合は更新必要
    }
    
    const now = new Date();
    const dataDate = new Date(source.year, source.month - 1);
    const daysDiff = (now - dataDate) / (1000 * 60 * 60 * 24);
    
    switch (source.frequency) {
      case 'yearly':
        return daysDiff > 365; // 1年以上経過
      case 'bimonthly':
        return daysDiff > 60; // 2ヶ月以上経過
      case 'irregular':
        return daysDiff > 30; // 1ヶ月以上経過
      default:
        return true;
    }
  }

  /**
   * 更新理由を取得
   */
  getUpdateReason(source, existingData) {
    if (!existingData || existingData.length === 0) {
      return 'データが存在しません';
    }
    
    const now = new Date();
    const dataDate = new Date(source.year, source.month - 1);
    const daysDiff = Math.floor((now - dataDate) / (1000 * 60 * 60 * 24));
    
    return `${daysDiff}日前のデータのため更新が必要`;
  }

  /**
   * 包括的なデータ更新を実行
   */
  async comprehensiveUpdate() {
    const startTime = Date.now();
    
    try {
      console.log('🚀 包括的国税庁データ更新を開始...');
      
      // 1. 全データソースを取得
      const allSources = await this.getAllDataSources();
      
      // 2. 優先順位を決定
      const prioritizedSources = this.prioritizeDataSources(allSources);
      
      // 3. 更新必要性をチェック
      const updateChecks = await this.checkUpdateNecessity(prioritizedSources);
      
      // 4. 更新が必要なデータのみ処理
      const updateResults = [];
      
      for (const check of updateChecks) {
        if (check.needsUpdate) {
          console.log(`📊 ${check.source.type}の更新を実行: ${check.reason}`);
          
          try {
            const result = await this.updateSpecificDataSource(check.source);
            updateResults.push({
              source: check.source,
              success: true,
              result
            });
          } catch (error) {
            console.error(`❌ ${check.source.type}の更新に失敗:`, error);
            updateResults.push({
              source: check.source,
              success: false,
              error: error.message
            });
          }
        } else {
          console.log(`✅ ${check.source.type}は最新です: ${check.reason}`);
        }
      }
      
      // 5. 結果を通知
      const duration = Date.now() - startTime;
      await this.sendUpdateNotification(updateResults, duration);
      
      console.log(`✅ 包括的データ更新完了: ${duration}ms`);
      return {
        success: true,
        updateResults,
        duration
      };
      
    } catch (error) {
      console.error('❌ 包括的データ更新に失敗:', error);
      throw error;
    }
  }

  /**
   * 特定のデータソースを更新
   */
  async updateSpecificDataSource(source) {
    try {
      console.log(`📥 ${source.type}のデータを取得中: ${source.url}`);
      
      // PDFファイルをダウンロード
      const pdfBuffer = await this.downloadPDF(source.url);
      
      // データタイプに応じて解析
      let extractedData;
      
      switch (source.type) {
        case 'annual_comparable':
          extractedData = await this.extractAnnualComparableData(pdfBuffer, source);
          break;
        case 'bimonthly_detailed':
          extractedData = await this.extractBimonthlyDetailedData(pdfBuffer, source);
          break;
        case 'amendment_notice':
          extractedData = await this.extractAmendmentNotice(pdfBuffer, source);
          break;
        default:
          throw new Error(`未知のデータタイプ: ${source.type}`);
      }
      
      // データを検証
      const validationResult = await this.validateExtractedData(extractedData, source.type);
      
      // データベースに保存
      const saveResult = await this.saveToDatabase(extractedData, source);
      
      // 更新履歴を記録
      await this.recordUpdateHistory(source, saveResult, validationResult);
      
      return {
        extractedData,
        validationResult,
        saveResult
      };
      
    } catch (error) {
      console.error(`❌ ${source.type}の更新に失敗:`, error);
      throw error;
    }
  }

  /**
   * 年次類似業種データを抽出
   */
  async extractAnnualComparableData(pdfBuffer, source) {
    // 既存のextractComparableIndustryDataと同様の処理
    // 年次データ用の特別な処理を追加
    return await this.extractComparableIndustryData(pdfBuffer, source.year, source.month);
  }

  /**
   * 2ヶ月ごとの詳細データを抽出
   */
  async extractBimonthlyDetailedData(pdfBuffer, source) {
    // 業種目別の詳細データを抽出
    // より細かい業種分類に対応
    return await this.extractDetailedIndustryData(pdfBuffer, source);
  }

  /**
   * 一部改正通達を抽出
   */
  async extractAmendmentNotice(pdfBuffer, source) {
    // 改正通達の内容を解析
    // 制度変更の影響を評価
    return await this.extractAmendmentData(pdfBuffer, source);
  }

  /**
   * 更新通知を送信
   */
  async sendUpdateNotification(updateResults, duration) {
    const successCount = updateResults.filter(r => r.success).length;
    const totalCount = updateResults.length;
    
    const message = {
      type: successCount === totalCount ? 'success' : 'warning',
      title: '包括的国税庁データ更新完了',
      message: `${successCount}/${totalCount}件のデータ更新が完了しました`,
      details: {
        duration: `${duration}ms`,
        results: updateResults.map(r => ({
          type: r.source.type,
          success: r.success,
          reason: r.error || '成功'
        }))
      }
    };
    
    await sendNotification(message);
  }
}

module.exports = { ComprehensiveNTAScraper }; 