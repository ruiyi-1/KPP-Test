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
  // 检查 Measurement ID 和 window 对象
  if (!GA_MEASUREMENT_ID || typeof window === 'undefined') {
    return false;
  }
  
  // 检查 gtag 函数是否存在且是真正的函数（不是我们的占位符）
  // 真正的 gtag 函数应该能发送网络请求
  if (!('gtag' in window) || typeof window.gtag !== 'function') {
    return false;
  }
  
  // 检查脚本是否已加载（通过检查 dataLayer 中是否有配置）
  if (!window.dataLayer || window.dataLayer.length === 0) {
    return false;
  }
  
  return true;
};

// 初始化 Google Analytics
export const initAnalytics = () => {
  if (!GA_MEASUREMENT_ID) {
    console.warn('[Analytics] GA_MEASUREMENT_ID not configured, analytics disabled');
    return;
  }

  // 初始化 dataLayer
  window.dataLayer = window.dataLayer || [];
  
  // 定义 gtag 函数（在脚本加载前作为占位符）
  function gtag(...args: any[]) {
    window.dataLayer.push(args);
  }
  
  // 在脚本加载完成前，使用占位符函数
  window.gtag = gtag;

  // 加载 Google Analytics 脚本
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  
  // 监听脚本加载完成
  script.onload = () => {
    // 脚本加载后，gtag 会被 Google Analytics 覆盖为真正的函数
    // 现在可以安全地调用配置
    window.gtag('js', new Date());
    window.gtag('config', GA_MEASUREMENT_ID, {
      // 配置选项
      send_page_view: true,
      anonymize_ip: true, // 匿名化 IP，保护隐私
      // 启用调试模式（开发环境）
      debug_mode: import.meta.env.DEV,
    });
  };
  
  // 监听脚本加载错误
  script.onerror = () => {
    if (import.meta.env.DEV) {
      console.error('[Analytics] Failed to load Google Analytics script');
    }
  };
  
  document.head.appendChild(script);
  
  // 在脚本加载前，先推送配置命令到 dataLayer
  // 这样当脚本加载完成后会自动处理这些命令
  window.dataLayer.push(['js', new Date()]);
  window.dataLayer.push(['config', GA_MEASUREMENT_ID, {
    send_page_view: true,
    anonymize_ip: true,
    debug_mode: import.meta.env.DEV,
  }]);
};

// 跟踪页面访问
export const trackPageView = (path: string, title?: string) => {
  if (!isAnalyticsEnabled()) return;

  window.gtag('config', GA_MEASUREMENT_ID, {
    page_path: path,
    page_title: title,
  });
};

// 跟踪自定义事件
export const trackEvent = (
  eventName: string,
  eventParams?: {
    [key: string]: string | number | boolean;
  }
) => {
  if (!isAnalyticsEnabled()) return;

  try {
    window.gtag('event', eventName, eventParams);
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('[Analytics] Error tracking event:', error);
    }
  }
};

// 跟踪用户操作
export const trackUserAction = (
  action: string,
  category: string = 'user_action',
  label?: string,
  value?: number
) => {
  // GA4 推荐使用标准参数名
  const params: { [key: string]: string | number | boolean } = {
    event_category: category, // 保留用于兼容性
    category: category, // GA4 标准参数
  };
  if (label !== undefined) {
    params.event_label = label; // 保留用于兼容性
    params.label = label; // GA4 标准参数
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

// 诊断函数：检查 GA 配置和连接（仅开发环境）
export const diagnoseAnalytics = () => {
  if (!import.meta.env.DEV) {
    console.warn('[Analytics] 诊断功能仅在开发环境可用');
    return;
  }

  console.group('[Analytics] 诊断信息');
  
  const scripts = Array.from(document.querySelectorAll('script[src*="googletagmanager"]'));
  const performanceEntries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
  const gaRequests = performanceEntries.filter(entry => 
    entry.name.includes('googletagmanager') || entry.name.includes('google-analytics')
  );
  const collectRequests = performanceEntries.filter(entry => 
    entry.name.includes('/collect') || entry.name.includes('/g/collect')
  );
  
  const result = {
    measurementId: GA_MEASUREMENT_ID,
    gtagLoaded: 'gtag' in window,
    dataLayerExists: !!window.dataLayer,
    dataLayerLength: window.dataLayer?.length || 0,
    scriptTagsFound: scripts.length,
    networkRequestsFound: gaRequests.length,
    collectRequestsFound: collectRequests.length,
  };
  
  console.log('诊断结果:', result);
  console.log('脚本标签:', scripts.length > 0 ? '✅ 已找到' : '❌ 未找到');
  console.log('网络请求:', gaRequests.length > 0 ? `✅ ${gaRequests.length} 个` : '❌ 未找到');
  console.log('数据收集:', collectRequests.length > 0 ? `✅ ${collectRequests.length} 个` : '⚠️ 未找到');
  
  console.groupEnd();
  
  return result;
};

// 在控制台暴露诊断函数（仅开发环境）
if (import.meta.env.DEV && typeof window !== 'undefined') {
  (window as any).diagnoseAnalytics = diagnoseAnalytics;
}
