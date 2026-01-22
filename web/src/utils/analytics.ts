/**
 * 站点访问统计工具
 * 支持 Google Analytics 4
 */

// 扩展 Window 接口以支持 gtag
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}

// Google Analytics 4 配置
const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID || '';

// 检查是否启用统计
const isAnalyticsEnabled = () => {
  return GA_MEASUREMENT_ID && typeof window !== 'undefined' && 'gtag' in window;
};

// 初始化 Google Analytics
export const initAnalytics = () => {
  if (!GA_MEASUREMENT_ID) {
    console.warn('[Analytics] GA_MEASUREMENT_ID not configured, analytics disabled');
    return;
  }

  // 加载 Google Analytics 脚本
  const script1 = document.createElement('script');
  script1.async = true;
  script1.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script1);

  // 初始化 gtag
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(...args: any[]) {
    window.dataLayer.push(args);
  };

  window.gtag('js', new Date());
  window.gtag('config', GA_MEASUREMENT_ID, {
    // 配置选项
    send_page_view: true,
    anonymize_ip: true, // 匿名化 IP，保护隐私
  });

  console.log('[Analytics] Google Analytics initialized');
};

// 跟踪页面访问
export const trackPageView = (path: string, title?: string) => {
  if (!isAnalyticsEnabled()) return;

  window.gtag('config', GA_MEASUREMENT_ID, {
    page_path: path,
    page_title: title,
  });

  console.log('[Analytics] Page view tracked:', { path, title });
};

// 跟踪自定义事件
export const trackEvent = (
  eventName: string,
  eventParams?: {
    [key: string]: string | number | boolean;
  }
) => {
  if (!isAnalyticsEnabled()) return;

  window.gtag('event', eventName, eventParams);
  console.log('[Analytics] Event tracked:', eventName, eventParams);
};

// 跟踪用户操作
export const trackUserAction = (
  action: string,
  category: string = 'user_action',
  label?: string,
  value?: number
) => {
  const params: { [key: string]: string | number | boolean } = {
    event_category: category,
  };
  if (label !== undefined) {
    params.event_label = label;
  }
  if (value !== undefined) {
    params.value = value;
  }
  trackEvent(action, params);
};

// 跟踪练习相关事件
export const trackPractice = {
  start: () => trackEvent('practice_start', { event_category: 'practice' }),
  next: (questionNumber: number) =>
    trackEvent('practice_next', {
      event_category: 'practice',
      question_number: questionNumber,
    }),
  previous: (questionNumber: number) =>
    trackEvent('practice_previous', {
      event_category: 'practice',
      question_number: questionNumber,
    }),
  submit: (isCorrect: boolean) =>
    trackEvent('practice_submit', {
      event_category: 'practice',
      is_correct: isCorrect,
    }),
  addToWrongSet: (questionId: string) =>
    trackEvent('practice_add_to_wrong_set', {
      event_category: 'practice',
      question_id: questionId,
    }),
  toggleTranslation: (show: boolean) =>
    trackEvent('practice_toggle_translation', {
      event_category: 'practice',
      show_translation: show,
    }),
};

// 跟踪考试相关事件
export const trackExam = {
  start: (questionCount: number, duration: number) =>
    trackEvent('exam_start', {
      event_category: 'exam',
      question_count: questionCount,
      duration_minutes: duration,
    }),
  pause: () => trackEvent('exam_pause', { event_category: 'exam' }),
  resume: () => trackEvent('exam_resume', { event_category: 'exam' }),
  submit: (score: number, passed: boolean, totalQuestions: number) =>
    trackEvent('exam_submit', {
      event_category: 'exam',
      score: score,
      passed: passed,
      total_questions: totalQuestions,
    }),
  timeUp: () => trackEvent('exam_time_up', { event_category: 'exam' }),
  exit: () => trackEvent('exam_exit', { event_category: 'exam' }),
};

// 跟踪错题集相关事件
export const trackWrongQuestions = {
  view: (count: number) =>
    trackEvent('wrong_questions_view', {
      event_category: 'wrong_questions',
      count: count,
    }),
  clearAll: (count: number) =>
    trackEvent('wrong_questions_clear_all', {
      event_category: 'wrong_questions',
      count: count,
    }),
  remove: (questionId: string) =>
    trackEvent('wrong_questions_remove', {
      event_category: 'wrong_questions',
      question_id: questionId,
    }),
  startPractice: (count: number) =>
    trackEvent('wrong_questions_start_practice', {
      event_category: 'wrong_questions',
      count: count,
    }),
};

// 跟踪设置相关事件
export const trackSettings = {
  changeLanguage: (language: string) =>
    trackEvent('settings_change_language', {
      event_category: 'settings',
      language: language,
    }),
  toggleTranslation: (enabled: boolean) =>
    trackEvent('settings_toggle_translation', {
      event_category: 'settings',
      translation_enabled: enabled,
    }),
  changeExamQuestionCount: (count: number) =>
    trackEvent('settings_change_exam_question_count', {
      event_category: 'settings',
      question_count: count,
    }),
  changePassingScore: (score: number) =>
    trackEvent('settings_change_passing_score', {
      event_category: 'settings',
      passing_score: score,
    }),
  changeExamDuration: (duration: number) =>
    trackEvent('settings_change_exam_duration', {
      event_category: 'settings',
      duration_minutes: duration,
    }),
};

// 跟踪错误
export const trackError = (error: Error, errorInfo?: string) => {
  trackEvent('error', {
    event_category: 'error',
    error_message: error.message,
    error_info: errorInfo || '',
  });
};
