import { useState, useEffect } from 'react';
import { NavBar, List, Card, Button, Dialog } from 'antd-mobile';
import { GlobalOutline, EyeInvisibleOutline, DeleteOutline } from 'antd-mobile-icons';
import { useTranslation } from 'react-i18next';
import { getWrongQuestions, removeWrongQuestion, clearWrongQuestions } from '../../utils';
import { WrongQuestion } from '../../types';
import { QuestionCard } from '../../components/QuestionCard/QuestionCard';
import { OptionItem } from '../../components/OptionItem/OptionItem';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import './WrongQuestions.css';

interface WrongQuestionsProps {
  onBack: () => void;
  onStartPractice: (questionIds: string[]) => void;
}

export const WrongQuestions = ({ onBack, onStartPractice }: WrongQuestionsProps) => {
  const { t } = useTranslation();
  const [wrongQuestions, setWrongQuestions] = useState<WrongQuestion[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<WrongQuestion | null>(null);
  const [showClearDialog, setShowClearDialog] = useState(false);
  const [showTranslation, setShowTranslation] = useLocalStorage('defaultShowTranslation', false);

  // 加载错题列表
  useEffect(() => {
    const loadWrongQuestions = () => {
      setWrongQuestions(getWrongQuestions());
    };
    loadWrongQuestions();

    // 监听 storage 变化
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'wrongQuestions') {
        loadWrongQuestions();
      }
    };
    window.addEventListener('storage', handleStorageChange);
    
    // 定期检查（用于同标签页内的更新）
    const interval = setInterval(loadWrongQuestions, 1000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  const handleRemoveQuestion = (questionId: string) => {
    removeWrongQuestion(questionId);
    setWrongQuestions(getWrongQuestions());
    if (selectedQuestion?.questionId === questionId) {
      setSelectedQuestion(null);
    }
  };

  const handleClearAll = () => {
    clearWrongQuestions();
    setWrongQuestions([]);
    setSelectedQuestion(null);
    setShowClearDialog(false);
  };

  const handleStartPractice = () => {
    const questionIds = wrongQuestions.map(wq => wq.questionId);
    onStartPractice(questionIds);
  };

  if (selectedQuestion) {
    // 显示单个错题的详细内容
    return (
      <div className="wrong-questions-page">
        <NavBar 
          onBack={() => setSelectedQuestion(null)}
          right={
            <div 
              className="nav-bar-icon"
              onClick={() => setShowTranslation(!showTranslation)}
              title={showTranslation ? t('practice.hideTranslation') : t('practice.showTranslation')}
            >
              {showTranslation ? (
                <EyeInvisibleOutline fontSize={20} />
              ) : (
                <GlobalOutline fontSize={20} />
              )}
            </div>
          }
        >
          {t('wrongQuestions.detail')}
        </NavBar>
        <div className="wrong-questions-content">
          <QuestionCard 
            question={selectedQuestion.question} 
            showTranslation={showTranslation}
          />
          <div className="options-container">
            {selectedQuestion.question.options.map((option) => (
              <OptionItem
                key={option.label}
                option={option}
                selected={option.label === selectedQuestion.userAnswer}
                correct={option.label === selectedQuestion.correctAnswer}
                showResult={true}
                showTranslation={showTranslation}
                questionId={selectedQuestion.question.id}
                questionTranslationKey={selectedQuestion.question.translationKey}
                onClick={() => {}}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 显示错题列表
  return (
    <div className="wrong-questions-page">
      <NavBar onBack={onBack}>
        {t('wrongQuestions.title')}
      </NavBar>
      <div className="wrong-questions-content">
        {wrongQuestions.length === 0 ? (
          <div className="empty-state">
            <p>{t('wrongQuestions.empty')}</p>
          </div>
        ) : (
          <>
            <div className="wrong-questions-header">
              <div className="wrong-questions-count">
                {t('wrongQuestions.total', { count: wrongQuestions.length })}
              </div>
              <div className="wrong-questions-actions">
                <Button
                  color="primary"
                  size="small"
                  onClick={handleStartPractice}
                  className="start-practice-button"
                >
                  {t('wrongQuestions.startPractice')}
                </Button>
                <Button
                  color="danger"
                  fill="outline"
                  size="small"
                  onClick={() => setShowClearDialog(true)}
                  className="clear-button"
                >
                  {t('wrongQuestions.clearAll')}
                </Button>
              </div>
            </div>
            <Card className="wrong-questions-list-card">
              <List>
                {wrongQuestions.map((wrongQuestion, index) => (
                  <List.Item
                    key={wrongQuestion.questionId}
                    extra={
                      <div
                        className="delete-icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveQuestion(wrongQuestion.questionId);
                        }}
                      >
                        <DeleteOutline fontSize={20} color="#ff4d4f" />
                      </div>
                    }
                    onClick={() => setSelectedQuestion(wrongQuestion)}
                    className="wrong-question-item"
                  >
                    <div className="wrong-question-preview">
                      <div className="question-text-preview">
                        <span className="wrong-question-index">{index + 1}.</span>
                        {wrongQuestion.question.question.substring(0, 50)}
                        {wrongQuestion.question.question.length > 50 ? '...' : ''}
                      </div>
                      <div className="answer-info-preview">
                        <span className="answer-label">{t('wrongQuestions.yourAnswer')}:</span>
                        <span className="answer-value wrong">{wrongQuestion.userAnswer}</span>
                        <span className="answer-separator">→</span>
                        <span className="answer-label">{t('wrongQuestions.correctAnswer')}:</span>
                        <span className="answer-value correct">{wrongQuestion.correctAnswer}</span>
                      </div>
                    </div>
                  </List.Item>
                ))}
              </List>
            </Card>
          </>
        )}
      </div>

      <Dialog
        visible={showClearDialog}
        content={t('wrongQuestions.clearConfirm', { count: wrongQuestions.length })}
        actions={[
          {
            key: 'cancel',
            text: t('practice.cancel'),
            onClick: () => setShowClearDialog(false),
          },
          {
            key: 'confirm',
            text: t('wrongQuestions.clearAll'),
            onClick: handleClearAll,
            danger: true,
          },
        ]}
        onClose={() => setShowClearDialog(false)}
      />
    </div>
  );
};
