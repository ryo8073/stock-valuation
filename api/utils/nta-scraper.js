// api/utils/nta-scraper.js
import fetch from 'node-fetch';
import { parse } from 'node-html-parser';
const { parsePDF } = require('./pdf-parser');
const { validateData } = require('./data-validator');
const { saveToDatabase } = require('./database');
const { sendNotification } = require('./notification');

/**
 * 国税庁データ自動取得・解析システム
 * 最新の類似業種比準価額データを取得し、データベースに保存
 */

class NTADataScraper {
  constructor() {
    this.baseUrl = 'https://www.nta.go.jp';
    this.dataUrl = 'https://www.nta.go.jp/law/tsutatsu/kobetsu/hyoka/zaisan.htm';
    this.pdfBaseUrl = 'https://www.nta.go.jp/law/tsutatsu/kobetsu/hyoka';
  }

  /**
   * 国税庁サイトから最新データの情報を取得
   */
  async getLatestDataInfo() {
    try {
      console.log('🔍 国税庁サイトから最新データ情報を取得中...');
      
      const response = await fetch(this.dataUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const html = await response.text();
      
      // 最新の類似業種比準価額データのリンクを抽出
      const latestDataMatch = html.match(/href="([^"]*r\d{2}\/\d{4}\/pdf\/[^"]*list_all\.pdf)"/);
      
      if (!latestDataMatch) {
        throw new Error('最新データのPDFリンクが見つかりませんでした');
      }
      
      const pdfUrl = this.baseUrl + latestDataMatch[1];
      const yearMatch = pdfUrl.match(/r(\d{2})\/(\d{4})/);
      
      if (!yearMatch) {
        throw new Error('データの年月を抽出できませんでした');
      }
      
      const year = parseInt('20' + yearMatch[1]); // r07 -> 2027
      const month = parseInt(yearMatch[2].substring(0, 2)); // 2506 -> 06 -> 6
      
      return {
        pdfUrl,
        year,
        month,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('❌ 最新データ情報の取得に失敗:', error);
      throw error;
    }
  }

  /**
   * PDFファイルをダウンロード
   */
  async downloadPDF(pdfUrl) {
    try {
      console.log(`📥 PDFファイルをダウンロード中: ${pdfUrl}`);
      
      const response = await fetch(pdfUrl);
      if (!response.ok) {
        throw new Error(`PDF download failed! status: ${response.status}`);
      }
      
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      
      console.log(`✅ PDFダウンロード完了: ${buffer.length} bytes`);
      return buffer;
      
    } catch (error) {
      console.error('❌ PDFダウンロードに失敗:', error);
      throw error;
    }
  }

  /**
   * PDFから類似業種比準価額データを抽出
   */
  async extractComparableIndustryData(pdfBuffer, year, month) {
    try {
      console.log('📊 類似業種比準価額データを抽出中...');
      
      const pdfText = await parsePDF(pdfBuffer);
      
      // 業種コードとデータを抽出する正規表現
      const industryDataRegex = /(\d{2})\s+([^\s]+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)/g;
      
      const extractedData = [];
      let match;
      
      while ((match = industryDataRegex.exec(pdfText)) !== null) {
        const [
          fullMatch,
          industryCode,
          industryName,
          averagePrice,
          averageDividend,
          averageProfit,
          averageNetAssets
        ] = match;
        
        extractedData.push({
          year,
          month,
          industry_code: industryCode,
          industry_name: industryName.trim(),
          average_price: parseFloat(averagePrice.replace(/,/g, '')),
          average_dividend: parseFloat(averageDividend.replace(/,/g, '')),
          average_profit: parseFloat(averageProfit.replace(/,/g, '')),
          average_net_assets: parseFloat(averageNetAssets.replace(/,/g, ''))
        });
      }
      
      console.log(`✅ 類似業種データ抽出完了: ${extractedData.length}件`);
      return extractedData;
      
    } catch (error) {
      console.error('❌ 類似業種データの抽出に失敗:', error);
      throw error;
    }
  }

  /**
   * PDFから配当還元率データを抽出
   */
  async extractDividendReductionRates(pdfBuffer, year, month) {
    try {
      console.log('📊 配当還元率データを抽出中...');
      
      const pdfText = await parsePDF(pdfBuffer);
      
      // 配当還元率データを抽出する正規表現
      const dividendDataRegex = /(\d{1,3}(?:,\d{3})*)\s*～\s*(\d{1,3}(?:,\d{3})*)\s+([\d,]+\.?\d*)/g;
      
      const extractedData = [];
      let match;
      
      while ((match = dividendDataRegex.exec(pdfText)) !== null) {
        const [fullMatch, minCapital, maxCapital, reductionRate] = match;
        
        extractedData.push({
          year,
          month,
          capital_range_min: parseInt(minCapital.replace(/,/g, '')),
          capital_range_max: parseInt(maxCapital.replace(/,/g, '')),
          reduction_rate: parseFloat(reductionRate.replace(/,/g, '')) / 100 // パーセントを小数に変換
        });
      }
      
      console.log(`✅ 配当還元率データ抽出完了: ${extractedData.length}件`);
      return extractedData;
      
    } catch (error) {
      console.error('❌ 配当還元率データの抽出に失敗:', error);
      throw error;
    }
  }

  /**
   * PDFから会社規模判定基準データを抽出
   */
  async extractCompanySizeCriteria(pdfBuffer, year, month) {
    try {
      console.log('📊 会社規模判定基準データを抽出中...');
      
      const pdfText = await parsePDF(pdfBuffer);
      
      // 会社規模判定基準を抽出する正規表現
      const sizeCriteriaRegex = /(製造業|卸売業|小売業|サービス業)\s+(小会社|中会社|大会社)\s+(\d+)\s*～\s*(\d+)\s+(\d+)\s*～\s*(\d+)\s+(\d+)\s*～\s*(\d+)/g;
      
      const extractedData = [];
      let match;
      
      while ((match = sizeCriteriaRegex.exec(pdfText)) !== null) {
        const [
          fullMatch,
          industryType,
          sizeCategory,
          employeeMin,
          employeeMax,
          assetMin,
          assetMax,
          salesMin,
          salesMax
        ] = match;
        
        extractedData.push({
          year,
          month,
          industry_type: industryType,
          size_category: sizeCategory,
          employee_min: parseInt(employeeMin),
          employee_max: parseInt(employeeMax),
          asset_min: parseInt(assetMin) * 10000, // 万円を円に変換
          asset_max: parseInt(assetMax) * 10000,
          sales_min: parseInt(salesMin) * 10000,
          sales_max: parseInt(salesMax) * 10000
        });
      }
      
      console.log(`✅ 会社規模判定基準データ抽出完了: ${extractedData.length}件`);
      return extractedData;
      
    } catch (error) {
      console.error('❌ 会社規模判定基準データの抽出に失敗:', error);
      throw error;
    }
  }

  /**
   * データの整合性をチェック
   */
  async validateExtractedData(comparableData, dividendData, sizeData) {
    try {
      console.log('🔍 抽出データの整合性をチェック中...');
      
      const validationResults = {
        comparable: validateData(comparableData, 'comparable_industry'),
        dividend: validateData(dividendData, 'dividend_reduction'),
        companySize: validateData(sizeData, 'company_size')
      };
      
      const allValid = Object.values(validationResults).every(result => result.isValid);
      
      if (!allValid) {
        console.warn('⚠️ データ検証で警告が発生しました:');
        Object.entries(validationResults).forEach(([type, result]) => {
          if (!result.isValid) {
            console.warn(`  ${type}: ${result.errors.join(', ')}`);
          }
        });
      }
      
      return validationResults;
      
    } catch (error) {
      console.error('❌ データ検証に失敗:', error);
      throw error;
    }
  }

  /**
   * データベースに保存
   */
  async saveToDatabase(comparableData, dividendData, sizeData, year, month) {
    try {
      console.log('💾 データベースに保存中...');
      
      const results = {
        comparable: await saveToDatabase('comparable_industry_data', comparableData, year, month),
        dividend: await saveToDatabase('dividend_reduction_rates', dividendData, year, month),
        companySize: await saveToDatabase('company_size_criteria', sizeData, year, month)
      };
      
      console.log('✅ データベース保存完了:');
      console.log(`  類似業種データ: ${results.comparable.inserted}件`);
      console.log(`  配当還元率データ: ${results.dividend.inserted}件`);
      console.log(`  会社規模判定基準: ${results.companySize.inserted}件`);
      
      return results;
      
    } catch (error) {
      console.error('❌ データベース保存に失敗:', error);
      throw error;
    }
  }

  /**
   * 更新履歴を記録
   */
  async recordUpdateHistory(dataInfo, results, validationResults) {
    try {
      const updateHistory = {
        check_date: new Date().toISOString(),
        data_type: 'all',
        last_modified: dataInfo.timestamp,
        update_available: true,
        update_status: 'completed',
        admin_approved: true,
        update_executed_at: new Date().toISOString(),
        record_count: {
          comparable: results.comparable.inserted,
          dividend: results.dividend.inserted,
          companySize: results.companySize.inserted
        },
        notes: `自動更新: ${dataInfo.year}年${dataInfo.month}月データ`
      };
      
      await saveToDatabase('update_history', [updateHistory]);
      console.log('✅ 更新履歴を記録しました');
      
    } catch (error) {
      console.error('❌ 更新履歴の記録に失敗:', error);
    }
  }

  /**
   * メイン処理: 国税庁データの自動取得・解析・保存
   */
  async updateNTAData() {
    const startTime = Date.now();
    
    try {
      console.log('🚀 国税庁データ自動更新を開始...');
      
      // 1. 最新データ情報を取得
      const dataInfo = await this.getLatestDataInfo();
      console.log(`📅 対象データ: ${dataInfo.year}年${dataInfo.month}月`);
      
      // 2. PDFファイルをダウンロード
      const pdfBuffer = await this.downloadPDF(dataInfo.pdfUrl);
      
      // 3. 各種データを抽出
      const comparableData = await this.extractComparableIndustryData(pdfBuffer, dataInfo.year, dataInfo.month);
      const dividendData = await this.extractDividendReductionRates(pdfBuffer, dataInfo.year, dataInfo.month);
      const sizeData = await this.extractCompanySizeCriteria(pdfBuffer, dataInfo.year, dataInfo.month);
      
      // 4. データの整合性をチェック
      const validationResults = await this.validateExtractedData(comparableData, dividendData, sizeData);
      
      // 5. データベースに保存
      const results = await this.saveToDatabase(comparableData, dividendData, sizeData, dataInfo.year, dataInfo.month);
      
      // 6. 更新履歴を記録
      await this.recordUpdateHistory(dataInfo, results, validationResults);
      
      // 7. 通知を送信
      const duration = Date.now() - startTime;
      await sendNotification({
        type: 'success',
        title: '国税庁データ更新完了',
        message: `${dataInfo.year}年${dataInfo.month}月のデータを更新しました`,
        details: {
          duration: `${duration}ms`,
          records: results,
          validation: validationResults
        }
      });
      
      console.log(`✅ 国税庁データ更新完了: ${duration}ms`);
      return {
        success: true,
        dataInfo,
        results,
        validationResults,
        duration
      };
      
    } catch (error) {
      console.error('❌ 国税庁データ更新に失敗:', error);
      
      // エラー通知を送信
      await sendNotification({
        type: 'error',
        title: '国税庁データ更新失敗',
        message: error.message,
        details: {
          timestamp: new Date().toISOString(),
          error: error.stack
        }
      });
      
      throw error;
    }
  }
}

module.exports = { NTADataScraper }; 