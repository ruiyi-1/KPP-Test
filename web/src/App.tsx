import { useState, useRef, useEffect } from 'react';
import { TabBar } from 'antd-mobile';
import { AppOutline, FileOutline, SetOutline } from 'antd-mobile-icons';
import { useTranslation } from 'react-i18next';
import { Practice } from './pages/Practice/Practice';
import { Exam, ExamHandle } from './pages/Exam/Exam';
import { Settings } from './pages/Settings/Settings';
import { WrongQuestions } from './pages/WrongQuestions/WrongQuestions';
import './App.css';

function App() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('practice'); // 默认显示练习页面
  const [showWrongQuestions, setShowWrongQuestions] = useState(false);
  const [practiceWrongQuestionIds, setPracticeWrongQuestionIds] = useState<string[] | undefined>(undefined);
  const examRef = useRef<ExamHandle>(null);
  const previousTabRef = useRef<string>('practice');

  // 监听打开错题集列表事件
  useEffect(() => {
    const handleOpenWrongQuestions = () => {
      setShowWrongQuestions(true);
    };

    window.addEventListener('openWrongQuestions', handleOpenWrongQuestions);
    return () => {
      window.removeEventListener('openWrongQuestions', handleOpenWrongQuestions);
    };
  }, []);

  // 检测tab切换
  useEffect(() => {
    // 如果从exam切换到其他tab，且考试正在进行，则暂停考试
    if (previousTabRef.current === 'exam' && activeTab !== 'exam') {
      // 使用setTimeout确保在组件状态更新后执行
      setTimeout(() => {
        if (examRef.current?.isExamInProgress()) {
          examRef.current.pauseExam();
        }
      }, 0);
    }
    
    // 如果切换回exam tab，且考试因tab切换而暂停，则显示恢复弹窗
    if (previousTabRef.current !== 'exam' && activeTab === 'exam') {
      // 使用setTimeout确保组件已经显示后再检查状态
      setTimeout(() => {
        if (examRef.current?.isPausedByTabSwitch()) {
          examRef.current.resumeExam();
        }
      }, 0);
    }

    previousTabRef.current = activeTab;
  }, [activeTab]);

  const handleTabChange = (key: string) => {
    setActiveTab(key);
    setShowWrongQuestions(false);
    setPracticeWrongQuestionIds(undefined);
  };

  const handleWrongQuestionsBack = () => {
    setShowWrongQuestions(false);
  };

  const handleStartPractice = (questionIds: string[]) => {
    setPracticeWrongQuestionIds(questionIds);
    setShowWrongQuestions(false);
    setActiveTab('practice');
  };

  // 如果显示错题集列表，覆盖其他页面
  if (showWrongQuestions) {
    return (
      <div className="app">
        <div className="content">
          <WrongQuestions onBack={handleWrongQuestionsBack} onStartPractice={handleStartPractice} />
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="content">
        <div style={{ visibility: activeTab === 'practice' ? 'visible' : 'hidden' }}>
          <Practice wrongQuestionIds={practiceWrongQuestionIds} />
        </div>
        <div style={{ visibility: activeTab === 'exam' ? 'visible' : 'hidden' }}>
          <Exam ref={examRef} />
        </div>
        <div style={{ visibility: activeTab === 'settings' ? 'visible' : 'hidden' }}>
          <Settings />
        </div>
      </div>
      <TabBar activeKey={activeTab} onChange={handleTabChange}>
        <TabBar.Item key="practice" icon={<AppOutline />} title={t('app.practice')} />
        <TabBar.Item key="exam" icon={<FileOutline />} title={t('app.exam')} />
        <TabBar.Item key="settings" icon={<SetOutline />} title={t('app.settings')} />
      </TabBar>
    </div>
  );
}

export default App;
