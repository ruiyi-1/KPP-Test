import { Question, WrongQuestion } from '../types';
import questionsData from '../data/questions.json';

export const getAllQuestions = (): Question[] => {
  return (questionsData as unknown as { questions: Question[] }).questions || [];
};

/**
 * Fisher-Yates 洗牌算法 - 更高效的随机打乱
 */
const shuffleArray = <T>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

export const getRandomQuestions = (count: number): Question[] => {
  const all = getAllQuestions();
  const shuffled = shuffleArray(all);
  return shuffled.slice(0, Math.min(count, all.length));
};

export const getQuestionById = (id: string): Question | undefined => {
  return getAllQuestions().find(q => q.id === id);
};

/**
 * 错题集管理工具函数
 */
const WRONG_QUESTIONS_KEY = 'wrongQuestions';

/**
 * 获取所有错题
 */
export const getWrongQuestions = (): WrongQuestion[] => {
  try {
    const stored = localStorage.getItem(WRONG_QUESTIONS_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Error reading wrong questions from localStorage:', error);
  }
  return [];
};

/**
 * 保存错题到 localStorage
 */
export const saveWrongQuestions = (wrongQuestions: WrongQuestion[]): void => {
  try {
    localStorage.setItem(WRONG_QUESTIONS_KEY, JSON.stringify(wrongQuestions));
  } catch (error) {
    console.error('Error saving wrong questions to localStorage:', error);
  }
};

/**
 * 添加错题
 */
export const addWrongQuestion = (question: Question, userAnswer: string, correctAnswer: string): void => {
  const wrongQuestions = getWrongQuestions();
  // 检查是否已存在
  const exists = wrongQuestions.some(wq => wq.questionId === question.id);
  if (!exists) {
    wrongQuestions.push({
      questionId: question.id,
      question,
      userAnswer,
      correctAnswer,
      addedAt: Date.now(),
    });
    saveWrongQuestions(wrongQuestions);
  }
};

/**
 * 删除错题
 */
export const removeWrongQuestion = (questionId: string): void => {
  const wrongQuestions = getWrongQuestions();
  const filtered = wrongQuestions.filter(wq => wq.questionId !== questionId);
  saveWrongQuestions(filtered);
};

/**
 * 清空错题集
 */
export const clearWrongQuestions = (): void => {
  localStorage.removeItem(WRONG_QUESTIONS_KEY);
};

/**
 * 检查题目是否在错题集中
 */
export const isQuestionInWrongSet = (questionId: string): boolean => {
  const wrongQuestions = getWrongQuestions();
  return wrongQuestions.some(wq => wq.questionId === questionId);
};
