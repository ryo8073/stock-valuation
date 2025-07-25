// api/utils/index.js
export { fetchNTAData, parseNTAData, validateData } from './nta-scraper.js';
export { 
  updateDatabase, 
  getCurrentData, 
  compareData, 
  getUpdateHistory,
  recordUpdateAttempt 
} from './database.js';