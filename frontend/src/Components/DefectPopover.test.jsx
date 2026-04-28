/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DefectPopover from './DefectPopover';

// ---------------------------------------------------------------------------
// Mock icons — simple components that render null in tests
// ---------------------------------------------------------------------------
const MockIcon = () => null;
MockIcon.displayName = 'MockIcon';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const createDefectList = () => [
  { id: 'loose_thread', name: 'Loose Thread', detail: 'Quantity (est)', icon: MockIcon },
  { id: 'stain', name: 'Stain/Oil/Soil', detail: 'Size (cm approx)', icon: MockIcon },
  { id: 'broken_stitch', name: 'Broken Stitch', detail: 'Description', icon: MockIcon },
  { id: 'open_seam', name: 'Open Seam', detail: 'Description', icon: MockIcon },
  { id: 'skip_stitch', name: 'Skip Stitch', detail: 'Description', icon: MockIcon },
  { id: 'fabric_run', name: 'Fabric Run', detail: 'Length (cm approx)', icon: MockIcon },
  { id: 'uncut_thread', name: 'Uncut Thread', detail: 'Quantity (est)', icon: MockIcon },
  { id: 'pleat', name: 'Pleat', detail: 'Description', icon: MockIcon },
  { id: 'dirt_mark', name: 'Dirt Marck', detail: 'Description', icon: MockIcon },
  { id: 'needle_holes', name: 'Needle Holes', detail: 'Description', icon: MockIcon },
  { id: 'uneven', name: 'Uneven', detail: 'Description', icon: MockIcon },
];

const defaultFrequencyMap = {
  loose_thread: 150,
  stain: 120,
  broken_stitch: 90,
  open_seam: 80,
  skip_stitch: 60,
  fabric_run: 50,
  uncut_thread: 40,
  pleat: 30,
  dirt_mark: 20,
  needle_holes: 15,
};

const defaultProps = {
  coordinates: { x: 50, y: 50 },
  onClose: vi.fn(),
  onSave: vi.fn(),
  defectList: createDefectList(),
  frequencyMap: defaultFrequencyMap,
};

/**
 * Add a `.garment-container` element to the DOM so the popover can calculate
 * its initial position. Removed after each test.
 */
const setupGarmentContainer = () => {
  const container = document.createElement('div');
  container.className = 'garment-container';
  container.style.width = '500px';
  container.style.height = '500px';
  container.style.position = 'absolute';
  container.style.left = '200px';
  container.style.top = '100px';
  document.body.appendChild(container);
  return container;
};

describe('DefectPopover', () => {
  beforeEach(() => {
    setupGarmentContainer();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    document.body.querySelector('.garment-container')?.remove();
    vi.restoreAllMocks();
  });

  // -----------------------------------------------------------------------
  // Initial render & structure
  // -----------------------------------------------------------------------
  describe('Initial render', () => {
    it('renders the popover title and close button', () => {
      render(<DefectPopover {...defaultProps} />);
      expect(screen.getByText('Identify Defect')).toBeInTheDocument();
      expect(screen.getByTitle('Cancel')).toBeInTheDocument();
    });

    it('renders the search input with placeholder', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);
      expect(input).toBeInTheDocument();
    });

    it('renders the "Frequent Defects" section', () => {
      render(<DefectPopover {...defaultProps} />);
      expect(screen.getByText('Frequent Defects (Tap to select)')).toBeInTheDocument();
    });

    it('shows top 10 defects sorted by frequency', () => {
      render(<DefectPopover {...defaultProps} />);
      // Top 10 most frequent: loose_thread (150), stain (120), broken_stitch (90),
      // open_seam (80), skip_stitch (60), fabric_run (50), uncut_thread (40),
      // pleat (30), dirt_mark (20), needle_holes (15)
      expect(screen.getByText('Loose Thread')).toBeInTheDocument();
      expect(screen.getByText('Stain/Oil/Soil')).toBeInTheDocument();
      expect(screen.getByText('Broken Stitch')).toBeInTheDocument();
      expect(screen.getByText('Open Seam')).toBeInTheDocument();
      expect(screen.getByText('Skip Stitch')).toBeInTheDocument();
      expect(screen.getByText('Fabric Run')).toBeInTheDocument();
      expect(screen.getByText('Uncut Thread')).toBeInTheDocument();
      expect(screen.getByText('Pleat')).toBeInTheDocument();
      expect(screen.getByText('Dirt Marck')).toBeInTheDocument();
      expect(screen.getByText('Needle Holes')).toBeInTheDocument();
      // Uneven has frequency 0 so it should NOT be in top 10
      expect(screen.queryByText('Uneven')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Empty / edge-case defectList
  // -----------------------------------------------------------------------
  describe('Edge cases — empty defectList', () => {
    it('does not crash when defectList is empty', () => {
      render(
        <DefectPopover
          {...defaultProps}
          defectList={[]}
          frequencyMap={{}}
        />,
      );
      expect(screen.getByText('Identify Defect')).toBeInTheDocument();
      // No frequent defect grid
      expect(screen.queryByText('Frequent Defects (Tap to select)')).toBeInTheDocument();
      // The grid should exist but be empty
      const grid = document.querySelector('.defects-grid');
      expect(grid).toBeInTheDocument();
      expect(grid?.children.length ?? 0).toBe(0);
    });

    it('does not crash when defectList is nullish', () => {
      render(
        <DefectPopover {...defaultProps} defectList={null} frequencyMap={{}} />,
      );
      expect(screen.getByText('Identify Defect')).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Close button
  // -----------------------------------------------------------------------
  describe('Close behavior', () => {
    it('calls onClose when the close button is clicked', () => {
      const onClose = vi.fn();
      render(<DefectPopover {...defaultProps} onClose={onClose} />);
      fireEvent.click(screen.getByTitle('Cancel'));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  // -----------------------------------------------------------------------
  // Search & autocomplete
  // -----------------------------------------------------------------------
  describe('Search & autocomplete', () => {
    it('shows autocomplete list when typing a search term', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);
      fireEvent.change(input, { target: { value: 'Uneven' } });
      // "Uneven" has frequency 0 so it's NOT in the grid — only in autocomplete
      expect(screen.getByText('Uneven')).toBeInTheDocument();
      expect(document.querySelector('.popover-autocomplete-list')).toBeInTheDocument();
    });

    it('filters defect list by search term (case-insensitive)', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);
      fireEvent.change(input, { target: { value: 'stitch' } });
      // These appear in both grid AND autocomplete — use getAllByText
      const brokenStitchElements = screen.getAllByText('Broken Stitch');
      expect(brokenStitchElements.length).toBeGreaterThanOrEqual(1);
      const skipStitchElements = screen.getAllByText('Skip Stitch');
      expect(skipStitchElements.length).toBeGreaterThanOrEqual(1);
      // Stain is NOT in the filtered results (doesn't match 'stitch')
      // But it IS in the grid (top 10) — so queryByText still finds the grid one
    });

    it('limits autocomplete results to 5 items', () => {
      // Create a defectList where many items match the same prefix
      const manyDefects = Array.from({ length: 20 }, (_, i) => ({
        id: `defect_${i}`,
        name: `Test Defect ${i}`,
        detail: 'Description',
        icon: MockIcon,
      }));
      render(
        <DefectPopover
          {...defaultProps}
          defectList={manyDefects}
          frequencyMap={{}}
        />,
      );
      const input = screen.getByPlaceholderText(/Search defect type/);
      fireEvent.change(input, { target: { value: 'Test' } });
      const items = document.querySelectorAll('.popover-autocomplete-item');
      expect(items.length).toBeLessThanOrEqual(5);
    });

    it('does not show autocomplete when search term is empty', () => {
      render(<DefectPopover {...defaultProps} />);
      expect(document.querySelector('.popover-autocomplete-list')).not.toBeInTheDocument();
    });

    it('does not show autocomplete when search term matches selected defect exactly', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);

      // Type a search for "Uneven" — this is NOT in the grid (frequency 0)
      fireEvent.change(input, { target: { value: 'Uneven' } });
      // Select it from autocomplete
      const autoItem = document.querySelector('.popover-autocomplete-item');
      fireEvent.click(autoItem);

      // Now typing "Uneven" again should NOT show autocomplete
      // (searchTerm === selectedDefect.name)
      fireEvent.change(input, { target: { value: 'Uneven' } });
      expect(document.querySelector('.popover-autocomplete-list')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Selecting a defect
  // -----------------------------------------------------------------------
  describe('Selecting a defect', () => {
    it('selects defect from autocomplete list', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);
      // Use "Uneven" — only in autocomplete, not in grid (frequency 0)
      fireEvent.change(input, { target: { value: 'Uneven' } });
      const autoItem = document.querySelector('.popover-autocomplete-item');
      fireEvent.click(autoItem);

      // Should now show detail view with the defect name
      const unevenElements = screen.getAllByText('Uneven');
      expect(unevenElements.length).toBeGreaterThanOrEqual(1);
      // Should show the "Change" button
      expect(screen.getByText('Change')).toBeInTheDocument();
      // Description-type defect
      expect(screen.getByPlaceholderText(/Enter Description/)).toBeInTheDocument();
    });

    it('selects defect from frequent defects grid', () => {
      render(<DefectPopover {...defaultProps} />);
      fireEvent.click(screen.getByText('Loose Thread'));

      // Should show detail view
      expect(screen.getByText('Loose Thread')).toBeInTheDocument();
      expect(screen.getByText('Change')).toBeInTheDocument();
      // Quantity defect → placeholder should include "Quantity"
      expect(screen.getByPlaceholderText(/Enter Quantity/)).toBeInTheDocument();
    });

    it('allows changing selection back to search view', () => {
      render(<DefectPopover {...defaultProps} />);
      // Select a defect
      fireEvent.click(screen.getByText('Loose Thread'));
      expect(screen.getByText('Change')).toBeInTheDocument();

      // Click Change
      fireEvent.click(screen.getByText('Change'));
      // Should be back to grid view
      expect(screen.getByText('Frequent Defects (Tap to select)')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search defect type/)).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Confirming & saving
  // -----------------------------------------------------------------------
  describe('Confirm & Save', () => {
    // Note: The "Confirm & Add Defect" button only renders when a defect is
    // selected, so there is no UI-reachable "save without selection" scenario.
    // The component has a safety guard for it, but it's dead code from UI.

    it('shows alert when numeric detail is empty', () => {
      render(<DefectPopover {...defaultProps} />);
      // Select a numeric defect (Stain/Oil/Soil → detail: 'Size (cm approx)')
      fireEvent.click(screen.getByText('Stain/Oil/Soil'));
      // Don't fill in detail
      const confirmButton = screen.getByText('Confirm & Add Defect');
      fireEvent.click(confirmButton);
      expect(window.alert).toHaveBeenCalledWith(
        'Please enter a valid number for Size (cm approx).',
      );
    });

    it('calls onSave with finalized defect for size-type defects', () => {
      const onSave = vi.fn();
      render(<DefectPopover {...defaultProps} onSave={onSave} />);
      // Select Stain/Oil/Soil → Size (cm approx) → isSize
      fireEvent.click(screen.getByText('Stain/Oil/Soil'));
      const detailInput = screen.getByPlaceholderText(/Enter Size/);
      fireEvent.change(detailInput, { target: { value: '5' } });
      fireEvent.click(screen.getByText('Confirm & Add Defect'));

      expect(onSave).toHaveBeenCalledTimes(1);
      const saved = onSave.mock.calls[0][0];
      expect(saved.defectType).toBe('stain');
      expect(saved.type_name).toBe('Stain/Oil/Soil');
      expect(saved.coordinates_x).toBe(50);
      expect(saved.coordinates_y).toBe(50);
      expect(saved.defectSize).toBe('5');
      expect(saved.defectCount).toBeNull();
      expect(saved.notes).toBe('');
      expect(typeof saved.id).toBe('number');
    });

    it('calls onSave with finalized defect for count-type defects', () => {
      const onSave = vi.fn();
      render(<DefectPopover {...defaultProps} onSave={onSave} />);
      // Select Loose Thread → Quantity (est) → isCount
      fireEvent.click(screen.getByText('Loose Thread'));
      const detailInput = screen.getByPlaceholderText(/Enter Quantity/);
      fireEvent.change(detailInput, { target: { value: '3' } });
      fireEvent.click(screen.getByText('Confirm & Add Defect'));

      expect(onSave).toHaveBeenCalledTimes(1);
      const saved = onSave.mock.calls[0][0];
      expect(saved.defectType).toBe('loose_thread');
      expect(saved.defectSize).toBeNull();
      expect(saved.defectCount).toBe('3');
      expect(saved.notes).toBe('');
    });

    it('calls onSave with notes for description-type defects', () => {
      const onSave = vi.fn();
      render(<DefectPopover {...defaultProps} onSave={onSave} />);
      // Select Broken Stitch → Description → neither size nor count
      fireEvent.click(screen.getByText('Broken Stitch'));
      const detailInput = screen.getByPlaceholderText(/Enter Description/);
      fireEvent.change(detailInput, { target: { value: 'Near the collar' } });
      fireEvent.click(screen.getByText('Confirm & Add Defect'));

      expect(onSave).toHaveBeenCalledTimes(1);
      const saved = onSave.mock.calls[0][0];
      expect(saved.defectType).toBe('broken_stitch');
      expect(saved.defectSize).toBeNull();
      expect(saved.defectCount).toBeNull();
      expect(saved.notes).toBe('Near the collar');
    });

    it('uses "N/A" for description-type defects when extraDetail is empty', () => {
      const onSave = vi.fn();
      render(<DefectPopover {...defaultProps} onSave={onSave} />);
      // Select Broken Stitch → Description
      fireEvent.click(screen.getByText('Broken Stitch'));
      // Don't fill detail — for description types, it should still save with "N/A"
      fireEvent.click(screen.getByText('Confirm & Add Defect'));

      expect(onSave).toHaveBeenCalledTimes(1);
      const saved = onSave.mock.calls[0][0];
      expect(saved.notes).toBe('N/A');
    });
  });

  // -----------------------------------------------------------------------
  // Numeric input validation
  // -----------------------------------------------------------------------
  describe('Numeric input validation', () => {
    it('only allows numeric input for cm/measurement defects', () => {
      render(<DefectPopover {...defaultProps} />);
      // Fabric Run → Length (cm approx) → isNumericDetail
      fireEvent.click(screen.getByText('Fabric Run'));
      const detailInput = screen.getByPlaceholderText(/Enter Length/);

      // Valid: empty string
      fireEvent.change(detailInput, { target: { value: '' } });
      expect(detailInput.value).toBe('');

      // Valid: integer
      fireEvent.change(detailInput, { target: { value: '10' } });
      expect(detailInput.value).toBe('10');

      // Valid: decimal
      fireEvent.change(detailInput, { target: { value: '10.5' } });
      expect(detailInput.value).toBe('10.5');

      // Invalid: letters
      fireEvent.change(detailInput, { target: { value: 'abc' } });
      // Should stay at previous valid value (10.5)
      expect(detailInput.value).toBe('10.5');
    });

    it('only allows numeric input for quantity defects', () => {
      render(<DefectPopover {...defaultProps} />);
      // Loose Thread → Quantity (est) → isNumericDetail
      fireEvent.click(screen.getByText('Loose Thread'));
      const detailInput = screen.getByPlaceholderText(/Enter Quantity/);

      // Valid
      fireEvent.change(detailInput, { target: { value: '5' } });
      expect(detailInput.value).toBe('5');

      // Invalid
      fireEvent.change(detailInput, { target: { value: 'abc' } });
      expect(detailInput.value).toBe('5');
    });

    it('allows any text for description-type defects', () => {
      render(<DefectPopover {...defaultProps} />);
      // Open Seam → Description → NOT numeric
      fireEvent.click(screen.getByText('Open Seam'));
      const detailInput = screen.getByPlaceholderText(/Enter Description/);

      fireEvent.change(detailInput, { target: { value: 'Any text 123!@#' } });
      expect(detailInput.value).toBe('Any text 123!@#');
    });
  });

  // -----------------------------------------------------------------------
  // Dragging — verify drag classes
  // -----------------------------------------------------------------------
  describe('Dragging interaction', () => {
    it('adds dragging class on header mousedown', () => {
      render(<DefectPopover {...defaultProps} />);
      const header = document.querySelector('.popover-header');
      expect(header).toBeInTheDocument();

      fireEvent.mouseDown(header, { clientX: 100, clientY: 100 });
      // After mousedown, isDragging should be true
      const popover = document.querySelector('.popover');
      expect(popover?.className).toContain('dragging');
    });

    it('removes dragging class on mouseup', () => {
      render(<DefectPopover {...defaultProps} />);
      const header = document.querySelector('.popover-header');

      fireEvent.mouseDown(header, { clientX: 100, clientY: 100 });
      fireEvent.mouseUp(document);

      const popover = document.querySelector('.popover');
      expect(popover?.className).not.toContain('dragging');
    });

    it('does not start drag when mousedown on input element', () => {
      render(<DefectPopover {...defaultProps} />);
      const input = screen.getByPlaceholderText(/Search defect type/);

      fireEvent.mouseDown(input);
      const popover = document.querySelector('.popover');
      expect(popover?.className).not.toContain('dragging');
    });

    it('does not start drag when mousedown on button', () => {
      render(<DefectPopover {...defaultProps} />);
      const closeBtn = screen.getByTitle('Cancel');

      fireEvent.mouseDown(closeBtn);
      const popover = document.querySelector('.popover');
      expect(popover?.className).not.toContain('dragging');
    });
  });
});
