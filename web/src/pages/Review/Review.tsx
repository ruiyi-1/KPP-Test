import { useState } from 'react';
import { NavBar } from 'antd-mobile';
import { useTranslation } from 'react-i18next';
import { QuestionCard } from '../../components/QuestionCard/QuestionCard';
import { getAllQuestions } from '../../utils';
import './Review.css';

export const Review = () => {
  const { t } = useTranslation();
  const questions = getAllQuestions();
  const [showTranslation, setShowTranslation] = useState(true);

  return (
    <div className="review-page">
      <NavBar back={null}>{t('review.title')}</NavBar>
      <div className="review-content">
        <div className="review-header">
          <h2>{t('review.allQuestions')} ({questions.length})</h2>
          <button
            className="toggle-button"
            onClick={() => setShowTranslation(!showTranslation)}
          >
            {showTranslation ? t('review.hideTranslation') : t('review.showTranslation')}
          </button>
        </div>
        <div className="questions-list">
          {questions.map((question, index) => (
            <div key={question.id} className="question-item">
              <div className="question-number">{t('review.questionNumber')} {index + 1}</div>
              <QuestionCard
                question={question}
                showTranslation={showTranslation}
              />
              <div className="correct-answer-info">
                {t('review.correctAnswer')}: {question.correctAnswer || t('review.notAvailable')}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
