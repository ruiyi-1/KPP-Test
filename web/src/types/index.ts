export interface Question {
  id: string;
  question: string;
  questionType: 'text' | 'image-options';
  options: Option[];
  correctAnswer: string | null;
  questionImages: string[];
  translationKey?: string; // 翻译key，用于i18n国际化
}

export interface Option {
  type: 'text' | 'image';
  label: string;
  content: string;
  imagePath?: string;
  translationKey?: string; // 选项的翻译key，用于i18n国际化
}

export interface Translation {
  question?: string;
  options?: Record<string, string>;
}

export interface ExamResult {
  total: number;
  correct: number;
  wrong: number;
  score: number;
  passed: boolean;
  wrongAnswers: WrongAnswer[];
}

export interface WrongAnswer {
  questionId: string;
  question: Question;
  userAnswer: string;
  correctAnswer: string;
}

export interface WrongQuestion {
  questionId: string;
  question: Question;
  userAnswer: string;
  correctAnswer: string;
  addedAt: number; // 时间戳
}
