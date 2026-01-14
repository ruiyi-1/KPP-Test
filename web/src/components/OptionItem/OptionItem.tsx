import { Card } from 'antd-mobile';
import { Option } from '../../types';
import { useTranslation } from 'react-i18next';
import { logger } from '../../utils/logger';
import './OptionItem.css';

interface OptionItemProps {
  option: Option;
  selected: boolean;
  correct: boolean;
  showResult: boolean;
  showTranslation?: boolean;
  questionId?: string;
  questionTranslationKey?: string; // 题目的翻译key
  onClick: () => void;
}

export const OptionItem = ({ 
  option, 
  selected, 
  correct, 
  showResult, 
  showTranslation = false,
  questionId,
  questionTranslationKey,
  onClick 
}: OptionItemProps) => {
  const { i18n } = useTranslation();

  const withBase = (p: string) => {
    if (!p) return p;
    if (p.startsWith('http://') || p.startsWith('https://') || p.startsWith('/')) return p;
    return `${import.meta.env.BASE_URL}${p}`;
  };
  
  const getOptionTranslation = (): string | null => {
    if (!showTranslation) {
      logger.log('[OptionItem] showTranslation is false, returning null');
      return null;
    }
    
    // 注意：useLocalStorage 使用 JSON.stringify 存储，所以需要解析
    let translationLanguage: string;
    try {
      const stored = localStorage.getItem('translationLanguage');
      translationLanguage = stored ? JSON.parse(stored) : i18n.language;
    } catch (error) {
      // 如果解析失败，尝试直接使用原始值（向后兼容）
      const stored = localStorage.getItem('translationLanguage');
      translationLanguage = stored || i18n.language;
    }
    logger.log('[OptionItem] Getting option translation', {
      optionLabel: option.label,
      optionContent: option.content.substring(0, 30) + '...',
      questionTranslationKey,
      questionId,
      translationLanguage
    });
    
    // 优先使用选项自己的translationKey
    if (option.translationKey) {
      try {
        const translationKey = `questions.${option.translationKey}.option`;
        const translation = i18n.getResource(translationLanguage, 'translation', translationKey);
        if (translation && typeof translation === 'string' && translation !== translationKey) {
          logger.log('[OptionItem] Found translation by option key:', translation);
          return translation;
        }
      } catch (error) {
        logger.error('[OptionItem] Error getting option translation by option key:', error);
      }
    }
    
    // 如果没有选项的translationKey，通过题目的translationKey获取
    // 翻译key格式：questions.{questionTranslationKey}.options.{optionLabel}
    // 如果没有questionTranslationKey，尝试使用questionId作为fallback（向后兼容）
    const keyToUse = questionTranslationKey || questionId;
    if (keyToUse) {
      try {
        const translationKey = `questions.${keyToUse}.options.${option.label}`;
        logger.log('[OptionItem] Looking for translation with key:', translationKey);
        
        // 检查questions资源
        const questionsResource = i18n.getResource(translationLanguage, 'translation', 'questions');
        if (questionsResource && keyToUse in questionsResource) {
          const questionData = questionsResource[keyToUse];
          logger.log('[OptionItem] Question data found:', questionData);
          if (questionData && questionData.options && option.label in questionData.options) {
            const translation = questionData.options[option.label];
            logger.log('[OptionItem] Option translation found:', translation);
            return translation;
          }
        }
        
        const translation = i18n.getResource(translationLanguage, 'translation', translationKey);
        logger.log('[OptionItem] Translation result:', {
          translation,
          type: typeof translation,
          isString: typeof translation === 'string',
          isNotKey: translation !== translationKey
        });
        
        if (translation && typeof translation === 'string' && translation !== translationKey) {
          logger.log('[OptionItem] Found translation by question key:', translation);
          return translation;
        }
      } catch (error) {
        logger.error('[OptionItem] Error getting option translation by question key:', error);
      }
    } else {
      logger.warn('[OptionItem] No keyToUse (questionTranslationKey or questionId)');
    }
    
    logger.log('[OptionItem] No translation found, returning null');
    return null;
  };

  const optionTranslation = getOptionTranslation();

  const getCardStyle = () => {
    if (!showResult) {
      return selected ? { border: '2px solid #1677ff' } : {};
    }
    if (correct) {
      return { border: '2px solid #52c41a', backgroundColor: '#f6ffed' };
    }
    if (selected && !correct) {
      return { border: '2px solid #ff4d4f', backgroundColor: '#fff2f0' };
    }
    return {};
  };

  return (
    <Card
      className="option-item"
      style={getCardStyle()}
      onClick={onClick}
    >
      <div className="option-content">
        <span className="option-label">{option.label}.</span>
        {option.type === 'text' ? (
          <div className="option-text-container">
            <span className="option-text">{option.content}</span>
            {showTranslation && optionTranslation && (
              <div className="option-translation">{optionTranslation}</div>
            )}
          </div>
        ) : (
          option.imagePath && (
            <img
              src={withBase(option.imagePath)}
              alt={`Option ${option.label}`}
              className="option-image"
            />
          )
        )}
      </div>
    </Card>
  );
};
