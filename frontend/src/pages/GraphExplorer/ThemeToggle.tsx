import { useEffect, useRef } from 'react';
import { useThemeStore } from '@/store/themeStore';

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);
  const ref = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleToggle = () => {
    if (ref.current) {
      ref.current.animate(
        [{ transform: 'scale(1)' }, { transform: 'scale(0.9)' }, { transform: 'scale(1)' }],
        { duration: 200, easing: 'ease-in-out' },
      );
    }
    toggle();
  };

  return (
    <button
      ref={ref}
      className="theme-toggle"
      onClick={handleToggle}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      <span style={{
        position: 'absolute', left: 4, top: '50%', transform: 'translateY(-50%)',
        fontSize: 12, lineHeight: 1, pointerEvents: 'none',
      }}>☀</span>
      <span style={{
        position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)',
        fontSize: 12, lineHeight: 1, pointerEvents: 'none',
      }}>☾</span>
    </button>
  );
}
