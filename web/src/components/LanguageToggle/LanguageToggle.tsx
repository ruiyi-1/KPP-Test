import { GlobalOutline, EyeInvisibleOutline } from 'antd-mobile-icons';
import { useTranslation } from 'react-i18next';
import './LanguageToggle.css';

interface LanguageToggleProps {
  showTranslation: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export const LanguageToggle = ({ showTranslation, onToggle, disabled }: LanguageToggleProps) => {
  const { t } = useTranslation();
  return (
    <button
      className={`language-toggle-icon ${showTranslation ? 'active' : ''}`}
      onClick={onToggle}
      disabled={disabled}
      title={showTranslation ? t('practice.hideTranslation') : t('practice.showTranslation')}
      aria-label={showTranslation ? t('practice.hideTranslation') : t('practice.showTranslation')}
    >
      {showTranslation ? (
        <EyeInvisibleOutline fontSize={20} />
      ) : (
        <GlobalOutline fontSize={20} />
      )}
    </button>
  );
};
