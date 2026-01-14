import { Card } from 'antd-mobile';
import { Question } from '../../types';
import { useTranslation } from 'react-i18next';
import { logger } from '../../utils/logger';
import './QuestionCard.css';

interface QuestionCardProps {
  question: Question;
  showTranslation: boolean;
}

export const QuestionCard = ({ question, showTranslation }: QuestionCardProps) => {
  const { i18n } = useTranslation();

  const withBase = (p: string) => {
    if (!p) return p;
    if (p.startsWith('http://') || p.startsWith('https://') || p.startsWith('/')) return p;
    return `${import.meta.env.BASE_URL}${p}`;
  };
  
  // 获取题目翻译
  const getQuestionTranslation = (): string | undefined => {
    logger.log('[QuestionCard] getQuestionTranslation called', {
      showTranslation,
      questionId: question.id,
      translationKey: question.translationKey,
      questionText: question.question.substring(0, 50) + '...'
    });
    
    if (!showTranslation) {
      logger.log('[QuestionCard] showTranslation is false, returning undefined');
      return undefined;
    }
    
    // 如果没有translationKey，尝试使用题目ID作为fallback（向后兼容）
    const translationKey = question.translationKey || question.id;
    if (!translationKey) {
      logger.warn('[QuestionCard] No translationKey or id found for question');
      return undefined;
    }
    
    // 使用 translationLanguage 而不是 i18n.language，这样界面语言切换不会影响题目翻译
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
    logger.log('[QuestionCard] Translation language:', translationLanguage);
    
    try {
      // 使用i18n的getResource获取翻译，key格式：questions.{translationKey}.question
      const fullKey = `questions.${translationKey}.question`;
      logger.log('[QuestionCard] Looking for translation with key:', fullKey);
      
      // 先检查questions资源是否存在
      const questionsResource = i18n.getResource(translationLanguage, 'translation', 'questions');
      logger.log('[QuestionCard] Questions resource exists:', !!questionsResource);
      if (questionsResource) {
        logger.log('[QuestionCard] Questions resource keys:', Object.keys(questionsResource));
        logger.log('[QuestionCard] Looking for key in questions:', translationKey);
        logger.log('[QuestionCard] Key exists in questions:', translationKey in questionsResource);
      }
      
      const translation = i18n.getResource(translationLanguage, 'translation', fullKey);
      logger.log('[QuestionCard] Translation result:', {
        translation,
        type: typeof translation,
        isString: typeof translation === 'string',
        isNotKey: translation !== fullKey
      });
      
      // 如果翻译存在且不是key本身，返回翻译
      if (translation && typeof translation === 'string' && translation !== fullKey) {
        logger.log('[QuestionCard] Translation found:', translation);
        return translation;
      }
      
      // 调试信息
      logger.warn('[QuestionCard] Translation not found:', {
        translationKey,
        fullKey,
        translationLanguage,
        hasTranslation: !!translation,
        translationValue: translation
      });
    } catch (error) {
      logger.error('[QuestionCard] Error getting question translation:', error);
    }
    
    return undefined;
  };

  const questionTranslation = getQuestionTranslation();

  return (
    <Card className="question-card">
      <div className="question-content">
        <div className="question-text">
          <div className="question-main">{question.question}</div>
          {showTranslation && questionTranslation && (
            <div className="question-translation">{questionTranslation}</div>
          )}
        </div>
        {question.questionImages && question.questionImages.length > 0 && (
          <div className="question-images">
            {question.questionImages.map((img, idx) => (
              <img
                key={idx}
                src={withBase(img)}
                alt={`Question image ${idx + 1}`}
                className="question-image"
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
