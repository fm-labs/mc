// components/ErrorBoundary.tsx
'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

type ErrorBoundaryProps = {
  /** Optional title to show in the fallback */
  title?: string;
  /** Custom fallback UI; if a function, it's called with the Error */
  fallback?: ReactNode | ((error: Error) => ReactNode);
  /** Called when an error is caught */
  onError?: (error: Error, info: ErrorInfo) => void;
  /** Called when the boundary is reset (via the button or resetKeys change) */
  onReset?: () => void;
  /** When any value in this array changes (by reference), the boundary resets */
  resetKeys?: ReadonlyArray<unknown>;
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
  info?: ErrorInfo;
};

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Report/log as needed
    if (this.props.onError) this.props.onError(error, info);
    if (process.env.NODE_ENV !== 'production') {
      // eslint-disable-next-line no-console
      console.error('[ErrorBoundary]', error, info);
    }
    this.setState({ info });
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    // Reset when resetKeys change
    const { resetKeys } = this.props;
    if (!this.state.hasError || !resetKeys || !prevProps.resetKeys) return;

    const changed =
      resetKeys.length !== prevProps.resetKeys.length ||
      resetKeys.some((v, i) => !Object.is(v, prevProps.resetKeys![i]));

    if (changed) this.reset();
  }

  reset = () => {
    this.setState({ hasError: false, error: undefined, info: undefined });
    this.props.onReset?.();
  };

  renderFallback() {
    const { title, fallback } = this.props;
    const { error, info } = this.state;

    if (typeof fallback === 'function') return fallback(error!);
    if (fallback) return fallback;

    return (
      <div className="rounded-md border text-sm border-red-600 bg-red-50 p-2 mb-2">
        <h4 className="font-bold text-red-700">
          {title ? `Error in ${title}` : 'Something went wrong'}
        </h4>
        <p className="mt-1 text-red-700">
          {error?.message || 'An unexpected error occurred.'}
        </p>

        <details className="mt-3 text-sm text-red-700/90">
          <summary className="cursor-pointer select-none">Show details</summary>
          <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs">
            {(error?.stack || '') + (info?.componentStack || '')}
          </pre>
        </details>

        <button
          type="button"
          onClick={this.reset}
          className="mt-3 inline-flex items-center rounded-md border border-red-600 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          Try again
        </button>
      </div>
    );
  }

  render() {
    return this.state.hasError ? this.renderFallback() : this.props.children;
  }
}

export default ErrorBoundary;
export { ErrorBoundary };
