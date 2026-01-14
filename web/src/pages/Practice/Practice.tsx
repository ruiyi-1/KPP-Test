import { useState, useEffect, useRef } from 'react';
import { Button, NavBar, Dialog, Input } from 'antd-mobile';
import { FileOutline, GlobalOutline, EyeInvisibleOutline } from 'antd-mobile-icons';
import { useTranslation } from 'react-i18next';
import { QuestionCard } from '../../components/QuestionCard/QuestionCard';
import { OptionItem } from '../../components/OptionItem/OptionItem';
import { getAllQuestions } from '../../utils';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { logger } from '../../utils/logger';
import './Practice.css';

export const Practice = () => {
  const { t } = useTranslation();
  const questions = getAllQuestions();
  const [lastPracticeIndex, setLastPracticeIndex] = useLocalStorage('lastPracticeIndex', 0);
  const [currentIndex, setCurrentIndex] = useState(lastPracticeIndex);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [showTranslation, setShowTranslation] = useLocalStorage('defaultShowTranslation', false);
  const [showJumpDialog, setShowJumpDialog] = useState(false);
  const [jumpInputValue, setJumpInputValue] = useState('');
  const contentRef = useRef<HTMLDivElement>(null);
  
  const currentQuestion = questions[currentIndex];

  // 恢复上次练习的题号
  useEffect(() => {
    if (lastPracticeIndex >= 0 && lastPracticeIndex < questions.length) {
      setCurrentIndex(lastPracticeIndex);
    }
  }, []);

  // 保存当前题号
  useEffect(() => {
    setLastPracticeIndex(currentIndex);
  }, [currentIndex, setLastPracticeIndex]);

  // 调试日志
  logger.log('[Practice] Component state:', {
    currentIndex,
    showTranslation,
    currentQuestionId: currentQuestion?.id,
    currentQuestionTranslationKey: currentQuestion?.translationKey,
    translationLanguage: localStorage.getItem('translationLanguage'),
    defaultShowTranslation: localStorage.getItem('defaultShowTranslation')
  });

  if (!currentQuestion) {
    return <div>{t('practice.noQuestionsAvailable')}</div>;
  }

  const handleOptionClick = (label: string) => {
    if (showResult) return;
    setSelectedAnswer(label);
    setShowResult(true);
  };

  // 滚动到顶部
  const scrollToTop = () => {
    if (contentRef.current) {
      contentRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setSelectedAnswer(null);
      setShowResult(false);
      scrollToTop();
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setSelectedAnswer(null);
      setShowResult(false);
      scrollToTop();
    }
  };

  const handleJumpToQuestion = (questionNumber: number) => {
    const targetIndex = questionNumber - 1; // 题目编号从1开始，索引从0开始
    if (targetIndex >= 0 && targetIndex < questions.length) {
      setCurrentIndex(targetIndex);
      setSelectedAnswer(null);
      setShowResult(false);
      setShowJumpDialog(false);
      setJumpInputValue('');
      scrollToTop();
    }
  };

  const handleJumpDialogConfirm = () => {
    const questionNum = parseInt(jumpInputValue.trim(), 10);
    if (isValidQuestionNumber(questionNum)) {
      handleJumpToQuestion(questionNum);
    }
  };

  const handleJumpDialogOpen = () => {
    setJumpInputValue(`${currentIndex + 1}`);
    setShowJumpDialog(true);
  };

  const isValidQuestionNumber = (num: number): boolean => {
    return !isNaN(num) && num >= 1 && num <= questions.length;
  };

  const getQuestionNumber = (): number | null => {
    const num = parseInt(jumpInputValue.trim(), 10);
    return isNaN(num) ? null : num;
  };

  const isInputValid = (): boolean => {
    const num = getQuestionNumber();
    return num !== null && isValidQuestionNumber(num);
  };

  const getErrorMessage = (): string | null => {
    const num = getQuestionNumber();
    if (num === null) {
      return null; // 空值不显示错误
    }
    if (num < 1) {
      return t('practice.questionNumberTooSmall');
    }
    if (num > questions.length) {
      return t('practice.questionNumberTooLarge', { count: questions.length });
    }
    return null;
  };

  const isCorrect = selectedAnswer === currentQuestion.correctAnswer;

  return (
    <div className="practice-page">
      <NavBar 
        back={null}
        left={
          <div className="nav-bar-icon" onClick={handleJumpDialogOpen}>
            <FileOutline fontSize={20} />
          </div>
        }
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
        {t('practice.title')}
      </NavBar>
      <div className="practice-content" ref={contentRef}>
        <div className="question-info">
          <span 
            className="question-number-link"
            onClick={handleJumpDialogOpen}
          >
            {t('practice.questionNumber')} {currentIndex + 1} {t('practice.of')} {questions.length}
          </span>
        </div>
        <Dialog
          visible={showJumpDialog}
          content={
            <div className="jump-dialog-content">
              <div className="jump-dialog-label">{t('practice.jumpToQuestion')}</div>
              <Input
                type="number"
                placeholder={t('practice.questionNumberRange', { count: questions.length })}
                value={jumpInputValue}
                onChange={(val) => setJumpInputValue(val)}
                onEnterPress={() => {
                  if (isInputValid()) {
                    handleJumpDialogConfirm();
                  }
                }}
                autoFocus
                className={!isInputValid() && jumpInputValue.trim() !== '' ? 'jump-input-error' : ''}
              />
              {getErrorMessage() && (
                <div className="jump-input-error-message">
                  {getErrorMessage()}
                </div>
              )}
            </div>
          }
          actions={[
            {
              key: 'cancel',
              text: t('practice.cancel'),
              onClick: () => {
                setShowJumpDialog(false);
                setJumpInputValue('');
              },
            },
            {
              key: 'confirm',
              text: t('practice.jump'),
              onClick: handleJumpDialogConfirm,
              disabled: !isInputValid(),
            },
          ]}
          onClose={() => {
            setShowJumpDialog(false);
            setJumpInputValue('');
          }}
        />
        <QuestionCard
          question={currentQuestion}
          showTranslation={showTranslation}
        />
        <div className="options-container">
          {currentQuestion.options.map((option) => (
            <OptionItem
              key={option.label}
              option={option}
              selected={selectedAnswer === option.label}
              correct={option.label === currentQuestion.correctAnswer}
              showResult={showResult}
              showTranslation={showTranslation}
              questionId={currentQuestion.id}
              questionTranslationKey={currentQuestion.translationKey}
              onClick={() => handleOptionClick(option.label)}
            />
          ))}
        </div>
        {showResult && (
          <div className={`result-message ${isCorrect ? 'correct' : 'wrong'}`}>
            {isCorrect ? t('practice.correct') : t('practice.wrong') + ' ' + currentQuestion.correctAnswer}
          </div>
        )}
      </div>
      <div className="navigation-buttons">
        <Button
          disabled={currentIndex === 0}
          onClick={handlePrevious}
        >
          {t('practice.previous')}
        </Button>
        <Button
          color="primary"
          disabled={currentIndex === questions.length - 1}
          onClick={handleNext}
        >
          {t('practice.next')}
        </Button>
      </div>
    </div>
  );
};
