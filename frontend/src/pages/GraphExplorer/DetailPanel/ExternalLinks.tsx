import type { NodeData } from '@/api/graph';

const SOURCE_URLS: Record<string, (id: string) => string> = {
  gene: (id) => `https://www.uniprot.org/uniprotkb?query=${id.replace('gene:', '')}`,
  protein: (id) => `https://www.uniprot.org/uniprotkb/${id.replace('protein:', '')}`,
  compound: (id) => `https://www.ebi.ac.uk/chembl/compound_report_card/${id.replace('compound:', '')}/`,
  disease: (id) => `https://platform.opentargets.org/disease/${id.replace('disease:', '')}`,
  article: (id) => `https://pubmed.ncbi.nlm.nih.gov/${id.replace('article:pmid:', '')}/`,
};

const SOURCE_LABELS: Record<string, string> = {
  gene: 'UniProt',
  protein: 'UniProt',
  compound: 'ChEMBL',
  disease: 'Open Targets',
  article: 'PubMed',
};

interface Props {
  node: NodeData | null;
}

export function ExternalLinks({ node }: Props) {
  if (!node) return null;
  const urlFn = SOURCE_URLS[node.type];
  if (!urlFn) return null;
  const url = urlFn(node.id);
  const sourceLabel = SOURCE_LABELS[node.type] ?? 'Source';

  return (
    <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--color-hairline)' }}>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          color: 'var(--color-primary)', fontSize: 12, fontWeight: 500,
          textDecoration: 'none', transition: 'opacity var(--transition-fast)',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
        View on {sourceLabel}
      </a>
    </div>
  );
}
