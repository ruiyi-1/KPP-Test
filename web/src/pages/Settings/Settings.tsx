import { useEffect, useRef, useState } from 'react';
import { NavBar, List, Card, Switch, Picker } from 'antd-mobile';
import { useTranslation } from 'react-i18next';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import { getWrongQuestions } from '../../utils';
import './Settings.css';

export const Settings = () => {
  const { i18n, t } = useTranslation();
  const [currentLanguage, setCurrentLanguage] = useLocalStorage('i18n_language', i18n.language);
  const [defaultShowTranslation, setDefaultShowTranslation] = useLocalStorage('defaultShowTranslation', false);
  const [autoAddToWrongSet, setAutoAddToWrongSet] = useLocalStorage('autoAddToWrongSet', true);
  const [examQuestionCount, setExamQuestionCount] = useLocalStorage('examQuestionCount', 50);
  const [passingScore, setPassingScore] = useLocalStorage('passingScore', 42);
  const [examDuration, setExamDuration] = useLocalStorage('examDuration', 45);
  const [wrongQuestionsCount, setWrongQuestionsCount] = useState(() => getWrongQuestions().length);

  // 监听错题集变化，更新数量显示
  useEffect(() => {
    const updateCount = () => {
      setWrongQuestionsCount(getWrongQuestions().length);
    };
    
    // 监听 storage 事件（跨标签页同步）
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'wrongQuestions') {
        updateCount();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    // 定期检查（用于同标签页内的更新）
    const interval = setInterval(updateCount, 1000);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, []);

  // 使用 useRef 保存之前的界面语言
  const prevLanguageRef = useRef(i18n.language);

  useEffect(() => {
    const prevLanguage = prevLanguageRef.current;
    
    // 如果语言没有改变，不需要做任何操作
    if (currentLanguage === prevLanguage) {
      return;
    }
    
    // 更新 i18n 语言
    i18n.changeLanguage(currentLanguage);
    
    // 更新之前的界面语言
    prevLanguageRef.current = currentLanguage;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLanguage]); // 只依赖 currentLanguage，避免循环更新

  const interfaceLanguages = [
    { label: 'English', value: 'en' },
    { label: '中文', value: 'zh' },
  ];

  const interfaceLanguageOptions = interfaceLanguages.map(lang => ({
    label: lang.label,
    value: lang.value,
  }));

  const examQuestionCountOptions = Array.from({ length: 19 }, (_, i) => ({
    label: `${(i + 1) * 5}`,
    value: `${(i + 1) * 5}`,
  }));

  const passingScoreOptions = Array.from({ length: examQuestionCount }, (_, i) => ({
    label: `${i + 1}`,
    value: `${i + 1}`,
  }));

  const examDurationOptions = Array.from({ length: 20 }, (_, i) => {
    const minutes = (i + 1) * 5;
    return {
      label: `${minutes} ${t('settings.minutes')}`,
      value: `${minutes}`,
    };
  });

  return (
    <div className="settings-page">
      <NavBar back={null}>{t('settings.title')}</NavBar>
      <div className="settings-content">
        <Card title={t('settings.language')} className="settings-card">
          <List>
            <Picker
              columns={[interfaceLanguageOptions]}
              value={[currentLanguage]}
              onConfirm={(val) => {
                if (val[0]) {
                  setCurrentLanguage(val[0] as string);
                  // 同步更新翻译语言
                  localStorage.setItem('translationLanguage', JSON.stringify(val[0]));
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.language')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : interfaceLanguageOptions.find(opt => opt.value === currentLanguage)?.label || ''
                  }
                />
              )}
            </Picker>
            <List.Item
              prefix={t('settings.defaultShowTranslation')}
              extra={
                <Switch
                  checked={defaultShowTranslation}
                  onChange={(checked) => setDefaultShowTranslation(checked)}
                />
              }
            />
          </List>
        </Card>

        <Card title={t('settings.practice')} className="settings-card">
          <List>
            <List.Item
              prefix={t('settings.autoAddToWrongSet')}
              extra={
                <Switch
                  checked={autoAddToWrongSet}
                  onChange={(checked) => setAutoAddToWrongSet(checked)}
                />
              }
            />
            <List.Item
              prefix={t('settings.wrongQuestionsList')}
              clickable
              onClick={() => {
                // 通过自定义事件通知 App 组件打开错题集列表
                window.dispatchEvent(new CustomEvent('openWrongQuestions'));
              }}
              extra={`${wrongQuestionsCount} ${t('settings.items')}`}
            />
          </List>
        </Card>

        <Card title={t('settings.examSettings')} className="settings-card">
          <List>
            <Picker
              columns={[examQuestionCountOptions]}
              value={[examQuestionCount.toString()]}
              onConfirm={(val) => {
                if (val[0]) {
                  const newCount = parseInt(val[0] as string, 10);
                  setExamQuestionCount(newCount);
                  if (passingScore > newCount) {
                    setPassingScore(newCount);
                  }
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.examQuestionCount')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : examQuestionCount.toString()
                  }
                />
              )}
            </Picker>
            <Picker
              columns={[passingScoreOptions]}
              value={[passingScore.toString()]}
              onConfirm={(val) => {
                if (val[0]) {
                  setPassingScore(parseInt(val[0] as string, 10));
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.passingScore')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : passingScore.toString()
                  }
                />
              )}
            </Picker>
            <Picker
              columns={[examDurationOptions]}
              value={[examDuration.toString()]}
              onConfirm={(val) => {
                if (val[0]) {
                  setExamDuration(parseInt(val[0] as string, 10));
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.examDuration')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : `${examDuration} ${t('settings.minutes')}`
                  }
                />
              )}
            </Picker>
          </List>
        </Card>

        <Card title={t('settings.about')} className="settings-card">
          <List>
            <List.Item
              prefix={t('settings.version')}
              extra="1.0.0"
            />
            <List.Item
              prefix={t('settings.github')}
              extra={
                <a
                  href="https://github.com/ruiyi-1/KPP-Test"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="github-link"
                >
                  {t('settings.githubAddress')}
                </a>
              }
            />
            <List.Item
              prefix={t('settings.donate')}
              clickable
              arrow={false}
              onClick={() => {
                window.open('https://qr.alipay.com/fkx10871ew38ukfqghwjx86', '_blank');
              }}
              extra={
                <span className="donate-link">{t('settings.donateText')}</span>
              }
            />
          </List>
        </Card>
      </div>
    </div>
  );
};
