import type { NodeData } from '@/api/graph';

const SOURCE_URLS: Record<string, (id: string) => string> = {
  gene: (id) => `https://www.uniprot.org/uniprotkb?query=${id.replace('gene:', '')}`,
  protein: (id) => `https://www.uniprot.org/uniprotkb/${id.replace('protein:', '')}`,
  compound: (id) => `https://www.ebi.ac.uk/chembl/compound_report_card/${id.replace('compound:', '')}/`,
  disease: (id) => `https://platform.opentargets.org/disease/${id.replace('disease:', '')}`,
  article: (id) => `https://pubmed.ncbi.nlm.nih.gov/${id.replace('pmid:', '')}/`,
};

interface Props {
  node: NodeData | null;
}

export function ExternalLinks({ node }: Props) {
  if (!node) return null;
  const urlFn = SOURCE_URLS[node.type];
  if (!urlFn) return null;
  const url = urlFn(node.id);
  return (
    <div style={{ marginTop: 16 }}>
      <a href={url} target="_blank" rel="noopener noreferrer"
         style={{ color: 'var(--color-primary)', fontSize: 13, textDecoration: 'none' }}>
        View in source database →
      </a>
    </div>
  );
}
