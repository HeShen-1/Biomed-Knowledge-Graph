import { useState, useRef, useEffect, useCallback } from 'react';
import type { Core } from 'cytoscape';
import { animate } from 'animejs';
import { useUiStore } from '@/store/uiStore';

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export function useBoxSelect(cy: Core | null) {
  const [rect, setRect] = useState<Rect | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const startRef = useRef<{ x: number; y: number } | null>(null);
  const rectRef = useRef<Rect | null>(null);
  const flashRef = useRef(false);

  const selectNodes = useUiStore((s) => s.selectNodes);
  const toggleNodeSelection = useUiStore((s) => s.toggleNodeSelection);
  const clearSelection = useUiStore((s) => s.clearSelection);

  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      if (!cy || e.button !== 0) return;
      const container = cy.container();
      if (!container) return;
      const target = e.target as HTMLElement;
      if (target !== container) return;

      const cr = container.getBoundingClientRect();
      startRef.current = { x: e.clientX - cr.left, y: e.clientY - cr.top };
      setIsSelecting(true);
      flashRef.current = false;
    },
    [cy],
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!startRef.current || !cy) return;
      const container = cy.container();
      if (!container) return;
      const cr = container.getBoundingClientRect();
      const cx = e.clientX - cr.left;
      const cy_ = e.clientY - cr.top;
      const s = startRef.current;

      const r: Rect = {
        x: Math.min(s.x, cx),
        y: Math.min(s.y, cy_),
        w: Math.abs(cx - s.x),
        h: Math.abs(cy_ - s.y),
      };
      rectRef.current = r;
      setRect(r);
    },
    [cy],
  );

  const handleMouseUp = useCallback(
    (e: MouseEvent) => {
      if (!startRef.current || !cy) return;
      setIsSelecting(false);
      startRef.current = null;

      const r = rectRef.current;
      if (!r || (r.w < 5 && r.h < 5)) {
        setRect(null);
        rectRef.current = null;
        return;
      }

      const ids: string[] = [];
      cy.nodes().forEach((node) => {
        const pos = node.renderedPosition();
        if (pos.x >= r.x && pos.x <= r.x + r.w && pos.y >= r.y && pos.y <= r.y + r.h) {
          ids.push(node.id());
        }
      });

      if (e.shiftKey) {
        if (ids.length > 0) {
          ids.forEach((id) => toggleNodeSelection(id));
        }
      } else if (ids.length > 0) {
        selectNodes(ids);
      } else {
        clearSelection();
      }

      flashRef.current = true;
      setRect({ ...r });
    },
    [cy, selectNodes, toggleNodeSelection, clearSelection],
  );

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && startRef.current) {
      startRef.current = null;
      setIsSelecting(false);
      setRect(null);
      rectRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!cy) return;
    const container = cy.container();
    if (!container) return;

    container.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [cy, handleMouseDown, handleMouseMove, handleMouseUp, handleKeyDown]);

  useEffect(() => {
    if (!flashRef.current || !rect || isSelecting) return;
    flashRef.current = false;

    const container = cy?.container();
    if (!container) return;

    requestAnimationFrame(() => {
      const el = container.querySelector('[data-box-select]');
      if (el instanceof HTMLElement) {
        animate(el, {
          opacity: [0.3, 0],
          duration: 250,
          easing: 'easeOutCubic',
          onComplete: () => {
            setRect(null);
            rectRef.current = null;
          },
        });
      } else {
        setRect(null);
        rectRef.current = null;
      }
    });
  }, [rect, isSelecting, cy]);

  return { isSelecting, rect };
}
