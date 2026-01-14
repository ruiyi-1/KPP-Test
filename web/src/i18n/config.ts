import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslations from './locales/en.json';
import zhTranslations from './locales/zh.json';
import { logger } from '../utils/logger';

// 从 localStorage 读取保存的语言设置
const getSavedLanguage = () => {
  const saved = localStorage.getItem('i18n_language');
  if (saved && (saved === 'en' || saved === 'zh')) {
    return saved;
  }
  return 'zh'; // 默认语言
};

// 尝试加载外部翻译文件（从 public 目录）
const loadExternalTranslations = async (lang: string): Promise<Record<string, any> | null> => {
  try {
    const publicPath = `${import.meta.env.BASE_URL}translations/${lang}.json`;
    const response = await fetch(publicPath);
    
    if (response.ok) {
      const data = await response.json();
      // 返回questions对象，格式：{ translationKey: { question: "...", options: { A: "...", B: "..." } } }
      return data.questions || null;
    } else {
      logger.warn(`[i18n] Failed to load translation file for ${lang}: ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    logger.error(`[i18n] Error loading translation file for ${lang}:`, error);
  }
  return null;
};

// 初始化 i18n
i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: enTranslations,
      },
      zh: {
        translation: zhTranslations,
      },
    },
    lng: getSavedLanguage(), // 从 localStorage 读取语言设置
    fallbackLng: 'zh',
    interpolation: {
      escapeValue: false,
    },
  });

// 异步加载外部翻译数据并合并到 i18n 资源中
(async () => {
  const languages = ['zh', 'en'];
  for (const lang of languages) {
    const externalTranslations = await loadExternalTranslations(lang);
    
    if (externalTranslations && typeof externalTranslations === 'object') {
      // 过滤掉注释键（以 _ 开头的键）
      const filteredTranslations = Object.keys(externalTranslations)
        .filter(key => !key.startsWith('_'))
        .reduce((acc, key) => {
          acc[key] = externalTranslations[key];
          return acc;
        }, {} as Record<string, any>);
      
      if (Object.keys(filteredTranslations).length > 0) {
        // 将外部翻译数据合并到 i18n 资源中
        // 翻译数据结构：questions.{translationKey}.question 和 questions.{translationKey}.options.{A/B/C}
        i18n.addResourceBundle(lang, 'translation', { questions: filteredTranslations }, true, true);
        logger.log(`[i18n] Loaded ${Object.keys(filteredTranslations).length} question translations for ${lang}`);
        
        // 如果当前语言是刚加载的语言，触发更新以通知组件
        const currentLang = i18n.language;
        if (currentLang === lang) {
          i18n.changeLanguage(lang).catch(err => {
            logger.error(`[i18n] Error triggering update for ${lang}:`, err);
          });
        }
      }
    }
  }
})();

export default i18n;
