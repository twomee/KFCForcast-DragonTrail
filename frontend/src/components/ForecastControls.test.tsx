import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ForecastControls } from './ForecastControls';

const stores = [
  { id: 1, name: 'Dizengoff Center' },
  { id: 2, name: 'Bnei Brak LYFE' },
];

describe('ForecastControls', () => {
  it('notifies callers when filters change and generation is requested', async () => {
    const onStoreChange = vi.fn();
    const onDateChange = vi.fn();
    const onGenerate = vi.fn();

    render(
      <ForecastControls
        stores={stores}
        selectedStoreId={1}
        selectedDate="2026-05-06"
        isGenerating={false}
        canGenerate={true}
        onStoreChange={onStoreChange}
        onDateChange={onDateChange}
        onGenerate={onGenerate}
      />,
    );

    await userEvent.selectOptions(screen.getByLabelText(/store/i), '2');
    fireEvent.change(screen.getByLabelText(/forecast date/i), {
      target: { value: '2026-05-07' },
    });
    await userEvent.click(screen.getByRole('button', { name: /generate/i }));

    expect(onStoreChange).toHaveBeenCalledWith(2);
    expect(onDateChange).toHaveBeenLastCalledWith('2026-05-07');
    expect(onGenerate).toHaveBeenCalledTimes(1);
  });

  it('disables the generate button while generation is running', () => {
    render(
      <ForecastControls
        stores={stores}
        selectedStoreId={1}
        selectedDate="2026-05-06"
        isGenerating={true}
        canGenerate={true}
        onStoreChange={vi.fn()}
        onDateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: /generating/i })).toBeDisabled();
  });

  it('disables the generate button when generation is not available', () => {
    render(
      <ForecastControls
        stores={stores}
        selectedStoreId={null}
        selectedDate=""
        isGenerating={false}
        canGenerate={false}
        onStoreChange={vi.fn()}
        onDateChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: /generate/i })).toBeDisabled();
  });
});
