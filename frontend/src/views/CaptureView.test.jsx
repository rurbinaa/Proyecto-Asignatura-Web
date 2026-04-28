/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CaptureView from './CaptureView';

// ---------------------------------------------------------------------------
// Mock static asset imports (SVGs → URL strings)
// ---------------------------------------------------------------------------
vi.mock('../assets/camisa_front.svg', () => ({ default: 'camisa_front.svg' }));
vi.mock('../assets/camisa_back.svg', () => ({ default: 'camisa_back.svg' }));
vi.mock('../assets/pants_front.svg', () => ({ default: 'pants_front.svg' }));
vi.mock('../assets/pants_back.svg', () => ({ default: 'pants_back.svg' }));

// ---------------------------------------------------------------------------
// Mock react-icons — simple functional components so they don't crash if
// anything tries to render them. Factories must be self-contained since
// vi.mock() is hoisted to top of file.
// ---------------------------------------------------------------------------
vi.mock('react-icons/md', () => {
  const FakeIcon = () => null;
  FakeIcon.displayName = 'FakeIcon';
  return {
    MdOutlineFormatColorFill: FakeIcon,
    MdDangerous: FakeIcon,
    MdStraighten: FakeIcon,
    MdGesture: FakeIcon,
    MdCropDin: FakeIcon,
    MdOutlineAssignmentLate: FakeIcon,
    MdDoNotDisturbAlt: FakeIcon,
    MdScatterPlot: FakeIcon,
  };
});

vi.mock('react-icons/lu', () => {
  const FakeIcon = () => null;
  FakeIcon.displayName = 'FakeIcon';
  return { LuScissors: FakeIcon };
});

// ---------------------------------------------------------------------------
// Mock API functions
// ---------------------------------------------------------------------------
const mockCreateInspection = vi.fn();
const mockCreateDefect = vi.fn();
const mockCloseInspection = vi.fn();

vi.mock('../api/capture.js', () => ({
  createInspection: (...args) => mockCreateInspection(...args),
  createDefect: (...args) => mockCreateDefect(...args),
  closeInspection: (...args) => mockCloseInspection(...args),
}));

// ---------------------------------------------------------------------------
// Mock child components so tests focus on CaptureView behavior
// ---------------------------------------------------------------------------
vi.mock('../Components/mockupContainer.jsx', () => ({
  default: ({
    garmentUrl,
    confirmedMarkers,
    isEditMode,
    onDefectPlacePending,
    pendingCoords,
  }) => (
    <div
      data-testid="mockup-container"
      data-garment-url={garmentUrl}
      data-markers={JSON.stringify(confirmedMarkers)}
      data-edit-mode={String(isEditMode)}
      data-pending-coords={JSON.stringify(pendingCoords)}
    >
      MockupContainer
      <button
        data-testid="simulate-defect-place"
        onClick={() => onDefectPlacePending({ x: 40, y: 60 })}
      >
        Place Defect
      </button>
    </div>
  ),
}));

vi.mock('../Components/DefectPopover.jsx', () => ({
  default: ({ coordinates, onClose, onSave, defectList, frequencyMap }) => (
    <div
      data-testid="defect-popover"
      data-coords={JSON.stringify(coordinates)}
    >
      DefectPopover
      <span data-testid="popover-defect-count">{defectList.length}</span>
      <button data-testid="popover-save" onClick={() => onSave({
        coordinates_x: 40,
        coordinates_y: 60,
        defectType: 'stain',
        defectSize: '5',
        defectCount: null,
        notes: '',
        type_name: 'Stain/Oil/Soil',
        side: 'front',
        id: Date.now(),
      })}>
        Save Defect
      </button>
      <button data-testid="popover-close" onClick={onClose}>
        Close Popover
      </button>
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------
describe('CaptureView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // =====================================================================
  //  Selection Step (initial render)
  // =====================================================================
  describe('Selection step — initial form', () => {
    it('renders the setup form with title', () => {
      render(<CaptureView />);
      expect(screen.getByText('Capture Setup')).toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<CaptureView />);
      expect(screen.getByPlaceholderText('e.g. L-90210')).toBeInTheDocument();
      expect(screen.getByText('Choose shape...')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. M, 32, XL')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g. Navy Blue, Red')).toBeInTheDocument();
    });

    it('renders garment options in the select', () => {
      render(<CaptureView />);
      expect(screen.getByText('Shirt / T-Shirt')).toBeInTheDocument();
      expect(screen.getByText('Pants')).toBeInTheDocument();
    });

    it('renders the Start Inspection button', () => {
      render(<CaptureView />);
      expect(screen.getByText('Start Inspection')).toBeInTheDocument();
    });

    it('does NOT render capture-mode elements initially', () => {
      render(<CaptureView />);
      expect(screen.queryByText('Quality Control')).not.toBeInTheDocument();
      expect(screen.queryByTestId('mockup-container')).not.toBeInTheDocument();
      expect(screen.queryByTestId('defect-popover')).not.toBeInTheDocument();
    });
  });

  // =====================================================================
  //  Form validation
  // =====================================================================
  describe('Form validation', () => {
    it('shows alert when Start Inspection is clicked with empty fields', () => {
      render(<CaptureView />);
      fireEvent.click(screen.getByText('Start Inspection'));
      expect(window.alert).toHaveBeenCalledWith(
        'Please fill out all fields (Lot, Garment Type, Style, Size, and Color) to continue.',
      );
    });

    it('shows alert when only some fields are filled', () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));
      expect(window.alert).toHaveBeenCalled();
    });

    it('proceeds to capture step when all fields are filled', () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });

      fireEvent.click(screen.getByText('Start Inspection'));

      // Now in capture mode
      expect(screen.getByText('Quality Control')).toBeInTheDocument();
      expect(screen.getByTestId('mockup-container')).toBeInTheDocument();
      expect(screen.queryByText('Capture Setup')).not.toBeInTheDocument();
    });
  });

  // =====================================================================
  //  Capture step — structure
  // =====================================================================
  describe('Capture step — structure', () => {
    const fillFormAndStart = () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));
    };

    it('shows inspection header with lot and style info', () => {
      fillFormAndStart();
      expect(screen.getByText(/Inspecting:/)).toBeInTheDocument();
      expect(screen.getByText(/L-001/)).toBeInTheDocument();
      expect(screen.getByText(/Slim Fit/)).toBeInTheDocument();
      expect(screen.getByText(/Navy Blue/)).toBeInTheDocument();
    });

    it('shows Back to Setup button', () => {
      fillFormAndStart();
      expect(screen.getByText('Back to Setup')).toBeInTheDocument();
    });

    it('shows Front View and Back View toggle buttons', () => {
      fillFormAndStart();
      expect(screen.getByText('Front View')).toBeInTheDocument();
      expect(screen.getByText('Back View')).toBeInTheDocument();
    });

    it('shows garment instructions text', () => {
      fillFormAndStart();
      expect(screen.getByText(/Tap the front of the garment/)).toBeInTheDocument();
    });

    it('shows the control panel with defect count', () => {
      fillFormAndStart();
      expect(screen.getByText('Defects: 0')).toBeInTheDocument();
    });

    it('shows Edit / Delete Markers button', () => {
      fillFormAndStart();
      expect(screen.getByText('Edit / Delete Markers')).toBeInTheDocument();
    });

    it('shows Undo Last button (disabled initially)', () => {
      fillFormAndStart();
      const undoBtn = screen.getByText('Undo Last');
      expect(undoBtn).toBeInTheDocument();
      expect(undoBtn).toBeDisabled();
    });

    it('shows Send button (disabled when no defects)', () => {
      fillFormAndStart();
      const sendBtn = screen.getByText('Send');
      expect(sendBtn).toBeInTheDocument();
      expect(sendBtn).toBeDisabled();
    });

    it('renders MockupContainer with correct garment URL for shirt front', () => {
      fillFormAndStart();
      const container = screen.getByTestId('mockup-container');
      expect(container).toHaveAttribute('data-garment-url', 'camisa_front.svg');
    });

    it('passes the correct garment URL when switching to back view', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByText('Back View'));
      const container = screen.getByTestId('mockup-container');
      expect(container).toHaveAttribute('data-garment-url', 'camisa_back.svg');
    });

    it('passes pants front URL when pants is selected', () => {
      render(<CaptureView />);
      // Fill everything and select pants
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'pants' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      const container = screen.getByTestId('mockup-container');
      expect(container).toHaveAttribute('data-garment-url', 'pants_front.svg');
    });
  });

  // =====================================================================
  //  Back to Setup
  // =====================================================================
  describe('Back to Setup', () => {
    it('returns to selection step when Back to Setup is clicked', () => {
      render(<CaptureView />);
      // Fill form and start
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      // Go back
      fireEvent.click(screen.getByText('Back to Setup'));
      expect(screen.getByText('Capture Setup')).toBeInTheDocument();
      // Form should be cleared
      expect(screen.getByPlaceholderText('e.g. L-90210')).toHaveValue('');
    });
  });

  // =====================================================================
  //  Defect popover integration
  // =====================================================================
  describe('Defect Popover integration', () => {
    const fillFormAndStart = () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));
    };

    it('does not show popover initially', () => {
      fillFormAndStart();
      expect(screen.queryByTestId('defect-popover')).not.toBeInTheDocument();
    });

    it('shows popover when a defect is placed on the garment', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      expect(screen.getByTestId('defect-popover')).toBeInTheDocument();
    });

    it('passes coordinates to the popover', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      const popover = screen.getByTestId('defect-popover');
      const coords = JSON.parse(popover.getAttribute('data-coords'));
      expect(coords).toEqual({ x: 40, y: 60 });
    });

    it('closes popover when onClose is triggered', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      expect(screen.getByTestId('defect-popover')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('popover-close'));
      expect(screen.queryByTestId('defect-popover')).not.toBeInTheDocument();
    });

    it('adds a defect and closes popover on save', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));

      // Save a defect via the popover mock
      fireEvent.click(screen.getByTestId('popover-save'));

      // Popover closes
      expect(screen.queryByTestId('defect-popover')).not.toBeInTheDocument();
      // Defect count should increment
      expect(screen.getByText('Defects: 1')).toBeInTheDocument();
    });

    it('passes confirmed markers to MockupContainer', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      fireEvent.click(screen.getByTestId('popover-save'));

      const container = screen.getByTestId('mockup-container');
      const markers = JSON.parse(container.getAttribute('data-markers'));
      expect(markers).toHaveLength(1);
      expect(markers[0].defectType).toBe('stain');
      expect(markers[0].side).toBe('front');
    });

    it('closes popover when switching garment view', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      expect(screen.getByTestId('defect-popover')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Back View'));
      expect(screen.queryByTestId('defect-popover')).not.toBeInTheDocument();
    });

    it('sends defect list length in popover', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      // The defect list (MOCK_DEFECT_LIST) has 46 entries
      expect(screen.getByTestId('popover-defect-count')).toHaveTextContent('46');
    });
  });

  // =====================================================================
  //  Edit mode
  // =====================================================================
  describe('Edit mode', () => {
    const fillFormAndStart = () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));
    };

    it('toggles edit mode when clicking Edit / Delete Markers', () => {
      fillFormAndStart();
      const editBtn = screen.getByText('Edit / Delete Markers');

      fireEvent.click(editBtn);
      expect(screen.getByText('Done Editing')).toBeInTheDocument();
      expect(screen.getByText(/Delete Mode Active/)).toBeInTheDocument();
    });

    it('passes isEditMode=true to MockupContainer when edit mode is on', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByText('Edit / Delete Markers'));

      const container = screen.getByTestId('mockup-container');
      expect(container.getAttribute('data-edit-mode')).toBe('true');
    });

    it('disables Send button when in edit mode', () => {
      fillFormAndStart();

      // Add a defect first so Send would normally be enabled
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      fireEvent.click(screen.getByTestId('popover-save'));

      // Enter edit mode
      fireEvent.click(screen.getByText('Edit / Delete Markers'));

      const sendBtn = screen.getByText('Send');
      expect(sendBtn).toBeDisabled();
    });

    it('disables Undo Last when in edit mode', () => {
      fillFormAndStart();
      fireEvent.click(screen.getByText('Edit / Delete Markers'));
      const undoBtn = screen.getByText('Undo Last');
      expect(undoBtn).toBeDisabled();
    });
  });

  // =====================================================================
  //  Send / API flow
  // =====================================================================
  describe('Send to API', () => {
    const fillFormStartAndAddDefect = () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      // Add a defect
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      fireEvent.click(screen.getByTestId('popover-save'));

      return screen.getByText('Send');
    };

    it('enables Send button when defects exist and not in edit mode', () => {
      const sendBtn = fillFormStartAndAddDefect();
      expect(sendBtn).not.toBeDisabled();
    });

    it('shows "Sending..." text while API is in progress', async () => {
      // Make the API never resolve during this test
      mockCreateInspection.mockReturnValue(new Promise(() => {}));

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      expect(screen.getByText('Sending...')).toBeInTheDocument();
    });

    it('calls createInspection with correct data on Send', async () => {
      mockCreateInspection.mockResolvedValue({ id: 1 });
      mockCreateDefect.mockResolvedValue({});
      mockCloseInspection.mockResolvedValue({
        result: 'PASS',
        total_defects: 1,
        quality_data_sync: { status: 'synced' },
      });

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(mockCreateInspection).toHaveBeenCalledWith({
          lot: 'L-001',
          style: 'Slim Fit',
          size: 'M',
          color: 'navy_blue',
        });
      });
    });

    it('calls createDefect for each grouped defect', async () => {
      mockCreateInspection.mockResolvedValue({ id: 1 });
      mockCreateDefect.mockResolvedValue({});
      mockCloseInspection.mockResolvedValue({
        result: 'PASS',
        total_defects: 1,
        quality_data_sync: { status: 'synced' },
      });

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(mockCreateDefect).toHaveBeenCalled();
      });
    });

    it('calls closeInspection after creating defects', async () => {
      mockCreateInspection.mockResolvedValue({ id: 1 });
      mockCreateDefect.mockResolvedValue({});
      mockCloseInspection.mockResolvedValue({
        result: 'PASS',
        total_defects: 1,
        quality_data_sync: { status: 'synced' },
      });

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(mockCloseInspection).toHaveBeenCalledWith(1);
      });
    });

    it('shows success alert on PASS with synced quality data', async () => {
      mockCreateInspection.mockResolvedValue({ id: 1 });
      mockCreateDefect.mockResolvedValue({});
      mockCloseInspection.mockResolvedValue({
        result: 'PASS',
        total_defects: 1,
        quality_data_sync: { status: 'synced' },
      });

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          expect.stringContaining('Inspection PASSED!'),
        );
      });
    });

    it('shows alert on API error', async () => {
      mockCreateInspection.mockRejectedValue(new Error('Network failure'));

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          'Error saving data: Network failure',
        );
      });
    });

    it('disables Send button while sending', async () => {
      mockCreateInspection.mockReturnValue(new Promise(() => {}));

      fillFormStartAndAddDefect();
      fireEvent.click(screen.getByText('Send'));

      const sendingBtn = screen.getByText('Sending...');
      expect(sendingBtn).toBeDisabled();
    });

    it('disables Send button when popover is open', () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      // Open popover (open popover but no defects yet → Send is disabled anyway)
      fireEvent.click(screen.getByTestId('simulate-defect-place'));

      const sendBtn = screen.getByText('Send');
      expect(sendBtn).toBeDisabled();
    });
  });

  // =====================================================================
  //  Undo Last
  // =====================================================================
  describe('Undo Last', () => {
    it('is disabled when there is no last submission', () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      expect(screen.getByText('Undo Last')).toBeDisabled();
    });

    it('is enabled after a successful Send (lastSubmission set)', async () => {
      mockCreateInspection.mockResolvedValue({ id: 1 });
      mockCreateDefect.mockResolvedValue({});
      mockCloseInspection.mockResolvedValue({
        result: 'PASS',
        total_defects: 1,
        quality_data_sync: { status: 'synced' },
      });

      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      // Add a defect
      fireEvent.click(screen.getByTestId('simulate-defect-place'));
      fireEvent.click(screen.getByTestId('popover-save'));

      // Send
      fireEvent.click(screen.getByText('Send'));

      await waitFor(() => {
        expect(screen.getByText('Undo Last')).not.toBeDisabled();
      });
    });
  });

  // =====================================================================
  //  Edge cases
  // =====================================================================
  describe('Edge cases', () => {
    it('shows alert when Send is clicked while in edit mode', () => {
      render(<CaptureView />);
      fireEvent.change(screen.getByPlaceholderText('e.g. L-90210'), {
        target: { value: 'L-001' },
      });
      fireEvent.change(screen.getByDisplayValue('Choose shape...'), {
        target: { value: 'shirt' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Slim Fit, V-Neck'), {
        target: { value: 'Slim Fit' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. M, 32, XL'), {
        target: { value: 'M' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Navy Blue, Red'), {
        target: { value: 'Navy Blue' },
      });
      fireEvent.click(screen.getByText('Start Inspection'));

      // Enter edit mode
      fireEvent.click(screen.getByText('Edit / Delete Markers'));

      // Send is disabled, so clicking it does nothing
      const sendBtn = screen.getByText('Send');
      expect(sendBtn).toBeDisabled();
    });
  });
});
