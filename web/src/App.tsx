import { useState, useRef, useEffect } from 'react';
import { TabBar } from 'antd-mobile';
import { AppOutline, FileOutline, SetOutline } from 'antd-mobile-icons';
import { useTranslation } from 'react-i18next';
import { Practice } from './pages/Practice/Practice';
import { Exam, ExamHandle } from './pages/Exam/Exam';
import { Settings } from './pages/Settings/Settings';
import './App.css';

function App() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('practice'); // 默认显示练习页面
  const examRef = useRef<ExamHandle>(null);
  const previousTabRef = useRef<string>('practice');

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
  };

  return (
    <div className="app">
      <div className="content">
        <div style={{ visibility: activeTab === 'practice' ? 'visible' : 'hidden' }}>
          <Practice />
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
