import { SearchPanel } from './SearchPanel/SearchPanel';
import { GraphCanvas } from './GraphCanvas/GraphCanvas';
import { DetailPanel } from './DetailPanel/DetailPanel';

export function GraphExplorer() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr 320px',
      gap: 'var(--space-3)',
      padding: 'var(--space-4)',
      minHeight: '100vh',
    }}>
      <div>
        <SearchPanel />
      </div>
      <div>
        <GraphCanvas />
      </div>
      <div>
        <DetailPanel />
      </div>
    </div>
  );
}
