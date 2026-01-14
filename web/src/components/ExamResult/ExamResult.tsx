import { Card, Button } from 'antd-mobile';
import { ExamResult as ExamResultType } from '../../types';
import { useTranslation } from 'react-i18next';
import './ExamResult.css';

interface ExamResultProps {
  result: ExamResultType;
  onReview: () => void;
  onRestart: () => void;
}

export const ExamResult = ({ result, onReview, onRestart }: ExamResultProps) => {
  const { t } = useTranslation();

  return (
    <div className="exam-result">
      <div className="result-card">
        <div className={`result-header ${result.passed ? 'passed' : 'failed'}`}>
          <h2>{result.passed ? t('exam.passed') : t('exam.failed')}</h2>
          <div className="score">{result.score}%</div>
          <div className="score-detail">
            {result.correct} / {result.total}
          </div>
        </div>
        <div className="result-stats">
          <div className="stat-item correct">
            <span className="stat-label">{t('exam.correct')}</span>
            <span className="stat-value">{result.correct}</span>
          </div>
          <div className="stat-item wrong">
            <span className="stat-label">{t('exam.wrong')}</span>
            <span className="stat-value">{result.wrong}</span>
          </div>
        </div>
        {result.wrongAnswers.length > 0 && (
          <div className="wrong-answers">
            <h3>{t('exam.wrongAnswersList')} ({result.wrongAnswers.length})</h3>
            <Button color="primary" onClick={onReview}>
              {t('exam.reviewWrongAnswers')}
            </Button>
          </div>
        )}
        <div className="result-actions">
          <Button color="primary" fill="outline" onClick={onRestart}>
            {t('exam.restart')}
          </Button>
        </div>
      </div>
    </div>
  );
};
