import { useEffect } from 'react';
import { animate } from 'animejs';
import type { Core } from 'cytoscape';
import { useUiStore } from '@/store/uiStore';

/*
| Key                    | Condition       | Action                                                       |
|------------------------|-----------------|--------------------------------------------------------------|
| Delete / Backspace     | has cy          | Remove selected elements, push history                       |
| Ctrl+Z                 | no input focused | uiStore.undo()                                               |
| Ctrl+Y / Ctrl+Shift+Z  | no input focused | uiStore.redo()                                               |
| Ctrl+A                 | has cy          | Select all visible nodes via uiStore.selectNodes             |
| Escape                 | —               | uiStore.clearSelection()                                     |
| F                      | has selection   | Fly-to: animate pan+zoom to selected, pulse ring 800ms        |
| + / =                  | has cy          | cy.zoom(zoom * 1.2), clamped                                 |
| -                      | has cy          | cy.zoom(zoom / 1.2), clamped                                 |
| Ctrl+K                 | —               | Focus search input[data-search]                              |
*/

function clamp(val: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, val));
}

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || (el as HTMLElement).contentEditable === 'true';
}

export function useKeyboard(cyRef: React.MutableRefObject<Core | null>) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const inputFocused = isInputFocused();

      if (inputFocused && e.key !== 'Escape' && !(e.ctrlKey && e.key === 'k')) {
        return;
      }

      const cy = cyRef.current;
      const uiStore = useUiStore.getState();

      // Delete / Backspace — remove selected nodes
      if ((e.key === 'Delete' || e.key === 'Backspace') && cy) {
        const selected = cy.$(':selected');
        if (selected.length > 0) {
          e.preventDefault();
          const selectedIds = selected.nodes().map((n) => n.id());
          const nodeCount = cy.nodes().length;
          const edgeCount = cy.edges().length;
          uiStore.pushHistory({
            action: 'remove',
            description: `Removed ${selectedIds.length} node(s)`,
            selectedNodeIds: selectedIds,
            nodeCount,
            edgeCount,
          });
          cy.remove(selected);
        }
        return;
      }

      // Ctrl+Z — undo
      if (e.ctrlKey && !e.shiftKey && e.key === 'z') {
        e.preventDefault();
        uiStore.undo();
        return;
      }

      // Ctrl+Y / Ctrl+Shift+Z — redo
      if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) {
        e.preventDefault();
        uiStore.redo();
        return;
      }

      // Ctrl+A — select all
      if (e.ctrlKey && e.key === 'a' && cy) {
        e.preventDefault();
        const allIds = cy.nodes().map((n) => n.id());
        uiStore.selectNodes(allIds);
        return;
      }

      // Escape — clear selection
      if (e.key === 'Escape') {
        uiStore.clearSelection();
        return;
      }

      // F — fly-to selected node
      if (e.key === 'f' && cy) {
        const selected = cy.$(':selected');
        if (selected.length > 0) {
          e.preventDefault();
          const node = selected.nodes()[0]!;
          const nodePos = node.renderedPosition();
          const startPan = cy.pan();
          const startZoom = cy.zoom();
          const targetZoom = clamp(startZoom * 1.5, 0.1, 5);
          const midX = cy.width() / 2;
          const midY = cy.height() / 2;
          const targetPan = {
            x: startPan.x + midX - nodePos.x,
            y: startPan.y + midY - nodePos.y,
          };

          const proxy = { panX: startPan.x, panY: startPan.y, zoom: startZoom };
          animate(proxy, {
            panX: targetPan.x,
            panY: targetPan.y,
            zoom: targetZoom,
            duration: 500,
            easing: 'easeOutExpo',
            update() {
              cy.pan({ x: proxy.panX, y: proxy.panY });
              cy.zoom(proxy.zoom);
            },
          });

          const container = cy.container();
          if (container) {
            const rect = container.getBoundingClientRect();
            const ripple = document.createElement('div');
            ripple.style.cssText = `
              position:absolute; pointer-events:none; z-index:10;
              left:${nodePos.x - 16 - container.offsetLeft + rect.left}px;
              top:${nodePos.y - 16 - container.offsetTop + rect.top}px;
              width:32px; height:32px; border-radius:50%;
              border:3px solid #f1c21b; opacity:0.6;
            `;
            container.appendChild(ripple);
            animate(ripple, {
              scale: [1, 3],
              opacity: [0.6, 0],
              duration: 800,
              easing: 'easeOutExpo',
              onComplete: () => ripple.remove(),
            });

            // Path highlight: light up connected edges sequentially
            const connEdges = node.connectedEdges();
            connEdges.forEach((edge, i) => {
              setTimeout(() => {
                const s = edge.style();
                s['line-color'] = '#f1c21b';
                s['width'] = 2.5;
                edge.style(s);
                setTimeout(() => {
                  s['line-color'] = '';
                  s['width'] = '';
                  edge.style(s);
                }, 1000);
              }, i * 80);
            });
          }
        }
        return;
      }

      // + / = — zoom in
      if ((e.key === '+' || e.key === '=') && cy) {
        e.preventDefault();
        const next = clamp(cy.zoom() * 1.2, 0.1, 5);
        cy.zoom(next);
        return;
      }

      // - — zoom out
      if (e.key === '-' && cy) {
        e.preventDefault();
        const next = clamp(cy.zoom() / 1.2, 0.1, 5);
        cy.zoom(next);
        return;
      }

      // Ctrl+K — focus search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.querySelector<HTMLInputElement>('input[data-search]')?.focus();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cyRef]);
}
