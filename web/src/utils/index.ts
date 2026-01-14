import { Question } from '../types';
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
