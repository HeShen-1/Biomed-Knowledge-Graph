import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchInput } from '@/pages/GraphExplorer/SearchPanel/SearchInput';

describe('SearchInput', () => {
  it('calls onChange with input value', () => {
    const handleChange = vi.fn();
    render(<SearchInput value="" onChange={handleChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'BRCA1' } });
    expect(handleChange).toHaveBeenCalledWith('BRCA1');
  });

  it('displays the current value', () => {
    render(<SearchInput value="TP53" onChange={vi.fn()} />);
    expect(screen.getByRole('textbox')).toHaveValue('TP53');
  });
});
