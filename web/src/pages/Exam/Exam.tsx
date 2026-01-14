import { useState, useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import { Button, NavBar, ProgressBar, Dialog } from 'antd-mobile';
import { useTranslation } from 'react-i18next';
import { QuestionCard } from '../../components/QuestionCard/QuestionCard';
import { OptionItem } from '../../components/OptionItem/OptionItem';
import { ExamResult } from '../../components/ExamResult/ExamResult';
import { Question, ExamResult as ExamResultType, WrongAnswer } from '../../types';
import { getRandomQuestions } from '../../utils';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import './Exam.css';

export interface ExamHandle {
  pauseExam: () => void;
  resumeExam: () => void;
  isExamInProgress: () => boolean;
  isPausedByTabSwitch: () => boolean;
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export const Exam = forwardRef<ExamHandle>((_, ref) => {
  const { t } = useTranslation();
  const [examQuestionCount] = useLocalStorage('examQuestionCount', 50);
  const [passingScore] = useLocalStorage('passingScore', 42);
  const [examDuration] = useLocalStorage('examDuration', 45);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [examStarted, setExamStarted] = useState(false);
  const [examFinished, setExamFinished] = useState(false);
  const [result, setResult] = useState<ExamResultType | null>(null);
  const [showReview, setShowReview] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [showPauseDialog, setShowPauseDialog] = useState(false);
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pauseStartTimeRef = useRef<number | null>(null);
  const totalPausedTimeRef = useRef<number>(0);
  const wasTabSwitchedRef = useRef<boolean>(false);

  // 暴露给父组件的方法
  useImperativeHandle(ref, () => ({
    pauseExam: () => {
      if (examStarted && !examFinished && !isPaused) {
        setIsPaused(true);
        pauseStartTimeRef.current = Date.now();
        wasTabSwitchedRef.current = true;
      }
    },
    resumeExam: () => {
      // 当切换回exam tab时，显示恢复弹窗
      if (wasTabSwitchedRef.current && isPaused) {
        setShowResumeDialog(true);
      }
    },
    isExamInProgress: () => {
      return examStarted && !examFinished;
    },
    isPausedByTabSwitch: () => {
      return wasTabSwitchedRef.current && isPaused;
    },
  }));

  const startExam = () => {
    const examQuestions = getRandomQuestions(examQuestionCount);
    setQuestions(examQuestions);
    setAnswers({});
    setCurrentIndex(0);
    setExamStarted(true);
    setExamFinished(false);
    setResult(null);
    setTimeRemaining(examDuration * 60);
    setIsPaused(false);
    setShowPauseDialog(false);
    setShowResumeDialog(false);
    totalPausedTimeRef.current = 0;
    pauseStartTimeRef.current = null;
    wasTabSwitchedRef.current = false;
  };

  const handleSubmit = useCallback(() => {
    let correct = 0;
    const wrongAnswers: WrongAnswer[] = [];

    questions.forEach((question) => {
      const userAnswer = answers[question.id];
      if (userAnswer === question.correctAnswer) {
        correct++;
      } else {
        wrongAnswers.push({
          questionId: question.id,
          question,
          userAnswer: userAnswer || '',
          correctAnswer: question.correctAnswer || '',
        });
      }
    });

    const score = Math.round((correct / questions.length) * 100);
    const passed = correct >= passingScore;

    setResult({
      total: questions.length,
      correct,
      wrong: questions.length - correct,
      score,
      passed,
      wrongAnswers,
    });

    setExamFinished(true);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [questions, answers]);

  // 倒计时逻辑
  useEffect(() => {
    if (examStarted && !examFinished && !isPaused && timeRemaining > 0) {
      timerRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            // 时间到，自动提交
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [examStarted, examFinished, isPaused]);

  // 时间到自动提交
  useEffect(() => {
    if (timeRemaining === 0 && examStarted && !examFinished) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      handleSubmit();
    }
  }, [timeRemaining, examStarted, examFinished, handleSubmit]);

  // Tab切换检测
  useEffect(() => {
    if (!examStarted || examFinished) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏，如果正在考试（未暂停），自动暂停并标记为tab切换
        if (!isPaused) {
          setIsPaused(true);
          pauseStartTimeRef.current = Date.now();
          wasTabSwitchedRef.current = true;
        }
      } else {
        // 页面显示
        if (wasTabSwitchedRef.current && isPaused && pauseStartTimeRef.current) {
          // 如果是因为tab切换导致的暂停，显示对话框询问退出或确认暂停
          setShowPauseDialog(true);
        } else if (isPaused && pauseStartTimeRef.current && !wasTabSwitchedRef.current) {
          // 如果之前已经确认暂停（非tab切换），显示恢复对话框
          setShowResumeDialog(true);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [examStarted, examFinished, isPaused]);


  const handlePauseConfirm = () => {
    setShowPauseDialog(false);
    // 确认暂停，清除tab切换标记，保持暂停状态
    wasTabSwitchedRef.current = false;
  };

  const handleExitExam = () => {
    setShowPauseDialog(false);
    setShowResumeDialog(false);
    setIsPaused(false);
    setExamStarted(false);
    setExamFinished(false);
    setResult(null);
    setQuestions([]);
    setAnswers({});
    setCurrentIndex(0);
    setTimeRemaining(0);
    totalPausedTimeRef.current = 0;
    pauseStartTimeRef.current = null;
    wasTabSwitchedRef.current = false;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleResumeExam = () => {
    setShowResumeDialog(false);
    setIsPaused(false);
    if (pauseStartTimeRef.current) {
      const pausedDuration = Date.now() - pauseStartTimeRef.current;
      totalPausedTimeRef.current += pausedDuration;
      pauseStartTimeRef.current = null;
    }
    wasTabSwitchedRef.current = false; // 清除tab切换标记
  };

  const handleOptionClick = (label: string) => {
    const questionId = questions[currentIndex].id;
    setAnswers({ ...answers, [questionId]: label });
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  if (!examStarted) {
    return (
      <div className="exam-page">
        <NavBar back={null}>{t('exam.title')}</NavBar>
        <div className="exam-start">
          <div className="exam-info">
            <h2>{t('exam.title')}</h2>
            <p>{t('exam.totalQuestions')}: {examQuestionCount}</p>
            <p>{t('exam.passingScore')}: {passingScore} / {examQuestionCount}</p>
            <p>{t('exam.duration')}: {examDuration} {t('settings.minutes')}</p>
            <p>{t('exam.translationDisabled')}</p>
          </div>
          <Button color="primary" size="large" onClick={startExam}>
            {t('exam.start')}
          </Button>
        </div>
      </div>
    );
  }

  if (examFinished && result) {
    if (showReview) {
      return (
        <div className="exam-page">
          <NavBar onBack={() => setShowReview(false)}>
            {t('exam.reviewWrongAnswers')}
          </NavBar>
          <div className="review-content">
            {result.wrongAnswers.map((wrong, idx) => {
              const userOption = wrong.question.options.find(opt => opt.label === wrong.userAnswer);
              const correctOption = wrong.question.options.find(opt => opt.label === wrong.correctAnswer);
              
              return (
                <div key={idx} className="wrong-answer-item">
                  <QuestionCard question={wrong.question} showTranslation={true} />
                  <div className="options-container">
                    {wrong.question.options.map((option) => {
                      const isUserAnswer = option.label === wrong.userAnswer;
                      const isCorrectAnswer = option.label === wrong.correctAnswer;
                      
                      return (
                        <OptionItem
                          key={option.label}
                          option={option}
                          selected={isUserAnswer}
                          correct={isCorrectAnswer}
                          showResult={true}
                          showTranslation={true}
                          questionId={wrong.question.id}
                          questionTranslationKey={wrong.question.translationKey}
                          onClick={() => {}}
                        />
                      );
                    })}
                  </div>
                  <div className="answer-info">
                    <div className="wrong-answer">
                      {t('exam.yourAnswer')}: {userOption ? `${userOption.label}. ${userOption.content}` : t('exam.notAnswered')}
                    </div>
                    <div className="correct-answer">
                      {t('exam.correctAnswer')}: {correctOption ? `${correctOption.label}. ${correctOption.content}` : wrong.correctAnswer}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    return (
      <div className="exam-page">
        <NavBar back={null}>{t('exam.examResult')}</NavBar>
        <ExamResult
          result={result}
          onReview={() => setShowReview(true)}
          onRestart={startExam}
        />
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const userAnswer = answers[currentQuestion.id];
  const progress = ((currentIndex + 1) / questions.length) * 100;
  
  // 计算已作答的题目数量
  const answeredCount = questions.filter(question => {
    const answer = answers[question.id];
    return answer && answer.trim() !== '';
  }).length;
  
  // 判断是否跳过了题目
  // 题目标号从1开始，已作答数量从0开始
  // 如果当前题目号 > 已作答数量 + 1，说明跳过了前面的题目
  const currentQuestionNumber = currentIndex + 1;
  const hasSkippedQuestions = currentQuestionNumber > answeredCount + 1;
  
  // 判断是否是最后一题
  const isLastQuestion = currentIndex === questions.length - 1;
  // 判断是否所有题目都有答案
  const allQuestionsAnswered = questions.every(question => {
    const answer = answers[question.id];
    return answer && answer.trim() !== '';
  });

  return (
    <div className="exam-page">
      <NavBar back={null}>{t('exam.title')}</NavBar>
      <div className="exam-content">
        <div className="exam-content-scrollable">
          <div className="exam-progress">
            <div className="progress-info">
              <span>
                {t('exam.questionNumber')} {currentIndex + 1} {t('exam.of')} {questions.length}
                <span className={`answered-count ${hasSkippedQuestions ? 'warning' : ''}`}>
                  · {t('exam.answered')}: {answeredCount} / {questions.length}
                </span>
              </span>
              <span className="time-remaining">
                {t('exam.timeRemaining')}: {formatTime(timeRemaining)}
              </span>
            </div>
            <ProgressBar percent={progress} />
          </div>
          {isPaused && (
            <div className="exam-paused-banner">
              {t('exam.examPaused')}
            </div>
          )}
          <QuestionCard question={currentQuestion} showTranslation={false} />
          <div className="options-container">
            {currentQuestion.options.map((option) => (
              <OptionItem
                key={option.label}
                option={option}
                selected={userAnswer === option.label}
                correct={false}
                showResult={false}
                showTranslation={false}
                questionId={currentQuestion.id}
                questionTranslationKey={currentQuestion.translationKey}
                onClick={() => handleOptionClick(option.label)}
              />
            ))}
          </div>
        </div>
        <div className="exam-navigation">
          <Button
            disabled={currentIndex === 0}
            onClick={handlePrevious}
          >
            {t('exam.previous')}
          </Button>
          {isLastQuestion ? (
            <Button
              color="primary"
              disabled={!allQuestionsAnswered}
              onClick={handleSubmit}
            >
              {t('exam.submit')}
            </Button>
          ) : (
            <Button
              color="primary"
              onClick={handleNext}
            >
              {t('exam.next')}
            </Button>
          )}
        </div>
      </div>
      <Dialog
        visible={showPauseDialog}
        content={t('exam.tabSwitchMessage')}
        actions={[
          [
            {
              key: 'pause',
              text: t('exam.pauseExam'),
              onClick: handlePauseConfirm,
            },
            {
              key: 'exit',
              text: t('exam.exitExam'),
              danger: true,
              onClick: handleExitExam,
            },
          ],
        ]}
      />
      <Dialog
        visible={showResumeDialog}
        content={t('exam.resumeExamMessage')}
        actions={[
          [
            {
              key: 'continue',
              text: t('exam.continueExam'),
              onClick: handleResumeExam,
            },
            {
              key: 'exit',
              text: t('exam.exitExam'),
              danger: true,
              onClick: handleExitExam,
            },
          ],
        ]}
      />
    </div>
  );
});

Exam.displayName = 'Exam';
