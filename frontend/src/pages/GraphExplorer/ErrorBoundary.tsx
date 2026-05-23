import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div style={{
          padding: 'var(--space-4)',
          borderRadius: 'var(--radius-md)',
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-hairline)',
          color: 'var(--color-ink-subtle)',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 120,
        }}>
          Something went wrong. Try refreshing the page.
        </div>
      );
    }

    return this.props.children;
  }
}
