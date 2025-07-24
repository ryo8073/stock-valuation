/**
 * 国税庁データ検証システム
 * 抽出されたデータの整合性と正確性を検証
 */

class DataValidator {
  constructor() {
    // 業種コードの定義
    this.industryCodes = {
      '01': '製造業',
      '02': '建設業', 
      '03': '卸売業',
      '04': '小売業',
      '05': 'サービス業',
      '06': '金融業',
      '07': '不動産業',
      '08': '運輸業',
      '09': '通信業',
      '10': '電気・ガス・水道業',
      '11': '農林水産業',
      '12': '鉱業'
    };
    
    // 会社規模の定義
    this.sizeCategories = ['小会社', '中会社', '大会社'];
    
    // 業種タイプの定義
    this.industryTypes = ['manufacturing', 'wholesale', 'retail', 'service'];
  }

  /**
   * 類似業種比準価額データの検証
   */
  validateComparableIndustryData(data) {
    const errors = [];
    const warnings = [];
    
    if (!Array.isArray(data) || data.length === 0) {
      errors.push('データが空または配列ではありません');
      return { isValid: false, errors, warnings };
    }
    
    data.forEach((record, index) => {
      // 必須フィールドのチェック
      if (!record.industry_code) {
        errors.push(`レコード${index + 1}: 業種コードがありません`);
      }
      
      if (!record.industry_name) {
        errors.push(`レコード${index + 1}: 業種名がありません`);
      }
      
      // 業種コードの妥当性チェック
      if (record.industry_code && !this.industryCodes[record.industry_code]) {
        warnings.push(`レコード${index + 1}: 未知の業種コード ${record.industry_code}`);
      }
      
      // 数値フィールドのチェック
      const numericFields = ['average_price', 'average_dividend', 'average_profit', 'average_net_assets'];
      numericFields.forEach(field => {
        if (typeof record[field] !== 'number' || isNaN(record[field])) {
          errors.push(`レコード${index + 1}: ${field}が数値ではありません`);
        } else if (record[field] < 0) {
          warnings.push(`レコード${index + 1}: ${field}が負の値です`);
        }
      });
      
      // 配当率の妥当性チェック
      if (record.average_dividend && (record.average_dividend < 0 || record.average_dividend > 100)) {
        warnings.push(`レコード${index + 1}: 配当率が異常な値です: ${record.average_dividend}%`);
      }
      
      // 年月のチェック
      if (!record.year || !record.month) {
        errors.push(`レコード${index + 1}: 年月が設定されていません`);
      } else {
        if (record.year < 2000 || record.year > 2030) {
          warnings.push(`レコード${index + 1}: 年が異常な値です: ${record.year}`);
        }
        if (record.month < 1 || record.month > 12) {
          errors.push(`レコード${index + 1}: 月が異常な値です: ${record.month}`);
        }
      }
    });
    
    // 重複チェック
    const duplicates = this.findDuplicates(data, 'industry_code');
    if (duplicates.length > 0) {
      errors.push(`重複する業種コード: ${duplicates.join(', ')}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      recordCount: data.length
    };
  }

  /**
   * 配当還元率データの検証
   */
  validateDividendReductionData(data) {
    const errors = [];
    const warnings = [];
    
    if (!Array.isArray(data) || data.length === 0) {
      errors.push('データが空または配列ではありません');
      return { isValid: false, errors, warnings };
    }
    
    data.forEach((record, index) => {
      // 必須フィールドのチェック
      if (!record.capital_range_min || !record.capital_range_max) {
        errors.push(`レコード${index + 1}: 資本金範囲が設定されていません`);
      }
      
      if (typeof record.reduction_rate !== 'number' || isNaN(record.reduction_rate)) {
        errors.push(`レコード${index + 1}: 還元率が数値ではありません`);
      }
      
      // 資本金範囲の妥当性チェック
      if (record.capital_range_min && record.capital_range_max) {
        if (record.capital_range_min >= record.capital_range_max) {
          errors.push(`レコード${index + 1}: 資本金範囲が不正です (min: ${record.capital_range_min}, max: ${record.capital_range_max})`);
        }
        
        if (record.capital_range_min < 0) {
          errors.push(`レコード${index + 1}: 資本金最小値が負の値です`);
        }
      }
      
      // 還元率の妥当性チェック
      if (record.reduction_rate && (record.reduction_rate < 0 || record.reduction_rate > 1)) {
        warnings.push(`レコード${index + 1}: 還元率が異常な値です: ${record.reduction_rate}`);
      }
      
      // 年月のチェック
      if (!record.year || !record.month) {
        errors.push(`レコード${index + 1}: 年月が設定されていません`);
      }
    });
    
    // 重複チェック
    const duplicates = this.findDuplicates(data, 'capital_range_min');
    if (duplicates.length > 0) {
      errors.push(`重複する資本金範囲: ${duplicates.join(', ')}`);
    }
    
    // 範囲の連続性チェック
    const sortedData = [...data].sort((a, b) => a.capital_range_min - b.capital_range_min);
    for (let i = 0; i < sortedData.length - 1; i++) {
      const current = sortedData[i];
      const next = sortedData[i + 1];
      
      if (current.capital_range_max !== next.capital_range_min) {
        warnings.push(`資本金範囲に隙間があります: ${current.capital_range_max} と ${next.capital_range_min}`);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      recordCount: data.length
    };
  }

  /**
   * 会社規模判定基準データの検証
   */
  validateCompanySizeData(data) {
    const errors = [];
    const warnings = [];
    
    if (!Array.isArray(data) || data.length === 0) {
      errors.push('データが空または配列ではありません');
      return { isValid: false, errors, warnings };
    }
    
    data.forEach((record, index) => {
      // 必須フィールドのチェック
      if (!record.industry_type) {
        errors.push(`レコード${index + 1}: 業種タイプが設定されていません`);
      }
      
      if (!record.size_category) {
        errors.push(`レコード${index + 1}: 会社規模カテゴリが設定されていません`);
      }
      
      // 業種タイプの妥当性チェック
      if (record.industry_type && !this.industryTypes.includes(record.industry_type)) {
        warnings.push(`レコード${index + 1}: 未知の業種タイプ: ${record.industry_type}`);
      }
      
      // 会社規模カテゴリの妥当性チェック
      if (record.size_category && !this.sizeCategories.includes(record.size_category)) {
        errors.push(`レコード${index + 1}: 不正な会社規模カテゴリ: ${record.size_category}`);
      }
      
      // 数値フィールドのチェック
      const numericFields = ['employee_min', 'employee_max', 'asset_min', 'asset_max', 'sales_min', 'sales_max'];
      numericFields.forEach(field => {
        if (record[field] !== null && record[field] !== undefined) {
          if (typeof record[field] !== 'number' || isNaN(record[field])) {
            errors.push(`レコード${index + 1}: ${field}が数値ではありません`);
          } else if (record[field] < 0) {
            warnings.push(`レコード${index + 1}: ${field}が負の値です`);
          }
        }
      });
      
      // 範囲の妥当性チェック
      if (record.employee_min && record.employee_max && record.employee_min >= record.employee_max) {
        errors.push(`レコード${index + 1}: 従業員数範囲が不正です`);
      }
      
      if (record.asset_min && record.asset_max && record.asset_min >= record.asset_max) {
        errors.push(`レコード${index + 1}: 資産範囲が不正です`);
      }
      
      if (record.sales_min && record.sales_max && record.sales_min >= record.sales_max) {
        errors.push(`レコード${index + 1}: 売上範囲が不正です`);
      }
      
      // 年月のチェック
      if (!record.year || !record.month) {
        errors.push(`レコード${index + 1}: 年月が設定されていません`);
      }
    });
    
    // 重複チェック
    const duplicates = this.findDuplicates(data, 'industry_type', 'size_category');
    if (duplicates.length > 0) {
      errors.push(`重複する業種・規模の組み合わせ: ${duplicates.join(', ')}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      recordCount: data.length
    };
  }

  /**
   * 重複チェック
   */
  findDuplicates(data, ...fields) {
    const seen = new Set();
    const duplicates = [];
    
    data.forEach(record => {
      const key = fields.map(field => record[field]).join('|');
      if (seen.has(key)) {
        duplicates.push(key);
      } else {
        seen.add(key);
      }
    });
    
    return [...new Set(duplicates)];
  }

  /**
   * データの統計情報を計算
   */
  calculateStatistics(data, type) {
    if (!Array.isArray(data) || data.length === 0) {
      return null;
    }
    
    const stats = {
      recordCount: data.length,
      yearRange: { min: Infinity, max: -Infinity },
      monthRange: { min: Infinity, max: -Infinity }
    };
    
    data.forEach(record => {
      if (record.year) {
        stats.yearRange.min = Math.min(stats.yearRange.min, record.year);
        stats.yearRange.max = Math.max(stats.yearRange.max, record.year);
      }
      
      if (record.month) {
        stats.monthRange.min = Math.min(stats.monthRange.min, record.month);
        stats.monthRange.max = Math.max(stats.monthRange.max, record.month);
      }
    });
    
    // タイプ別の統計情報
    switch (type) {
      case 'comparable_industry':
        stats.industryCodes = [...new Set(data.map(r => r.industry_code))];
        stats.averagePriceRange = this.calculateRange(data, 'average_price');
        stats.averageDividendRange = this.calculateRange(data, 'average_dividend');
        break;
        
      case 'dividend_reduction':
        stats.capitalRange = {
          min: Math.min(...data.map(r => r.capital_range_min)),
          max: Math.max(...data.map(r => r.capital_range_max))
        };
        stats.reductionRateRange = this.calculateRange(data, 'reduction_rate');
        break;
        
      case 'company_size':
        stats.industryTypes = [...new Set(data.map(r => r.industry_type))];
        stats.sizeCategories = [...new Set(data.map(r => r.size_category))];
        break;
    }
    
    return stats;
  }

  /**
   * 数値フィールドの範囲を計算
   */
  calculateRange(data, field) {
    const values = data.map(r => r[field]).filter(v => typeof v === 'number' && !isNaN(v));
    if (values.length === 0) return null;
    
    return {
      min: Math.min(...values),
      max: Math.max(...values),
      average: values.reduce((sum, val) => sum + val, 0) / values.length
    };
  }

  /**
   * データの整合性を総合的に検証
   */
  validateData(data, type) {
    let validationResult;
    
    switch (type) {
      case 'comparable_industry':
        validationResult = this.validateComparableIndustryData(data);
        break;
      case 'dividend_reduction':
        validationResult = this.validateDividendReductionData(data);
        break;
      case 'company_size':
        validationResult = this.validateCompanySizeData(data);
        break;
      default:
        throw new Error(`未知のデータタイプ: ${type}`);
    }
    
    // 統計情報を追加
    validationResult.statistics = this.calculateStatistics(data, type);
    
    return validationResult;
  }

  /**
   * データの品質スコアを計算
   */
  calculateQualityScore(validationResult) {
    let score = 100;
    
    // エラーによる減点
    score -= validationResult.errors.length * 10;
    
    // 警告による減点
    score -= validationResult.warnings.length * 2;
    
    // データ量による加点
    if (validationResult.recordCount > 100) {
      score += 5;
    } else if (validationResult.recordCount < 10) {
      score -= 10;
    }
    
    return Math.max(0, Math.min(100, score));
  }
}

module.exports = { DataValidator };

// 従来の関数との互換性を保つ
function validateData(data, type) {
  const validator = new DataValidator();
  return validator.validateData(data, type);
}

module.exports.validateData = validateData; 
} 