import { useEffect, useRef } from 'react';
import { NavBar, List, Card, Switch, Picker } from 'antd-mobile';
import { useTranslation } from 'react-i18next';
import { useLocalStorage } from '../../hooks/useLocalStorage';
import './Settings.css';

export const Settings = () => {
  const { i18n, t } = useTranslation();
  const [currentLanguage, setCurrentLanguage] = useLocalStorage('i18n_language', i18n.language);
  const [defaultShowTranslation, setDefaultShowTranslation] = useLocalStorage('defaultShowTranslation', false);
  const [translationLanguage, setTranslationLanguage] = useLocalStorage('translationLanguage', i18n.language);
  const [examQuestionCount, setExamQuestionCount] = useLocalStorage('examQuestionCount', 50);
  const [passingScore, setPassingScore] = useLocalStorage('passingScore', 42);
  const [examDuration, setExamDuration] = useLocalStorage('examDuration', 45);

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
    
    // 检查用户是否手动设置过翻译语言
    const hasManuallySet = localStorage.getItem('translationLanguageManuallySet') === 'true';
    
    // 如果用户没有手动设置过翻译语言，或者翻译语言和旧的界面语言一致，则同步更新翻译语言
    if (!hasManuallySet || translationLanguage === prevLanguage) {
      setTranslationLanguage(currentLanguage);
    }
    
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

  const availableTranslationLanguages = [
    { label: '中文', value: 'zh' },
    { label: 'English', value: 'en' },
  ];

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

  const translationLanguageOptions = availableTranslationLanguages.map(lang => ({
    label: lang.label,
    value: lang.value,
  }));

  return (
    <div className="settings-page">
      <NavBar back={null}>{t('settings.title')}</NavBar>
      <div className="settings-content">
        <Card title={t('settings.interfaceLanguage')} className="settings-card">
          <List>
            <Picker
              columns={[interfaceLanguageOptions]}
              value={[currentLanguage]}
              onConfirm={(val) => {
                if (val[0]) {
                  setCurrentLanguage(val[0] as string);
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.interfaceLanguage')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : interfaceLanguageOptions.find(opt => opt.value === currentLanguage)?.label || ''
                  }
                />
              )}
            </Picker>
          </List>
        </Card>

        <Card title={t('settings.translation')} className="settings-card">
          <List>
            <Picker
              columns={[translationLanguageOptions]}
              value={[translationLanguage]}
              onConfirm={(val) => {
                if (val[0]) {
                  setTranslationLanguage(val[0] as string);
                  // 标记用户已手动设置翻译语言
                  localStorage.setItem('translationLanguageManuallySet', 'true');
                }
              }}
            >
              {(items, { open }) => (
                <List.Item
                  prefix={t('settings.translationLanguage')}
                  clickable
                  onClick={open}
                  extra={
                    items[0] ? items[0].label : translationLanguageOptions.find(opt => opt.value === translationLanguage)?.label || ''
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
                  href="https://github.com"
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
