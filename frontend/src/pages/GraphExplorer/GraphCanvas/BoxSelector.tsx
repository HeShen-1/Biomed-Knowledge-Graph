interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export function BoxSelector({ rect }: { rect: Rect | null }) {
  if (!rect) return null;

  return (
    <div
      data-box-select
      style={{
        position: 'absolute',
        left: rect.x,
        top: rect.y,
        width: rect.w,
        height: rect.h,
        border: '1px solid var(--color-primary)',
        background: 'color-mix(in srgb, var(--color-primary) 8%, transparent)',
        pointerEvents: 'none',
        zIndex: 100,
      }}
    />
  );
}
