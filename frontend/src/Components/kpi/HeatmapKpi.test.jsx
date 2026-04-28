import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import HeatmapKpi from './HeatmapKpi';

describe('HeatmapKpi', () => {
  it('renders heatmap-kpi class', () => {
    const { container } = render(<HeatmapKpi />);
    expect(container.querySelector('.heatmap-kpi')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<HeatmapKpi title="Heatmap Title" />);
    expect(screen.getByText('Heatmap Title')).toBeInTheDocument();
  });

  it('does not render title when not provided', () => {
    const { container } = render(<HeatmapKpi data={[{ x: 'A', y: '1', value: 10 }]} />);
    expect(container.querySelector('h3')).not.toBeInTheDocument();
  });

  describe('empty state', () => {
    it('shows "No data" when data is empty array', () => {
      render(<HeatmapKpi data={[]} />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('shows "No data" when data is null', () => {
      render(<HeatmapKpi data={null} />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('shows "No data" when data is undefined', () => {
      render(<HeatmapKpi data={undefined} />);
      expect(screen.getByText('No data')).toBeInTheDocument();
    });

    it('does not render a table when data is empty', () => {
      const { container } = render(<HeatmapKpi data={[]} />);
      expect(container.querySelector('table')).not.toBeInTheDocument();
    });

    it('still renders title in empty state when provided', () => {
      render(<HeatmapKpi title="My Heatmap" data={[]} />);
      expect(screen.getByText('My Heatmap')).toBeInTheDocument();
      expect(screen.getByText('No data')).toBeInTheDocument();
    });
  });

  describe('table rendering', () => {
    const sampleData = [
      { x: 'A', y: '1', value: 10 },
      { x: 'A', y: '2', value: 20 },
      { x: 'B', y: '1', value: 30 },
      { x: 'B', y: '2', value: 40 },
    ];

    it('renders a table when data is provided', () => {
      const { container } = render(<HeatmapKpi data={sampleData} />);
      expect(container.querySelector('table')).toBeInTheDocument();
    });

    it('renders x-axis headers in the table header', () => {
      render(<HeatmapKpi data={sampleData} />);
      // The first th is blank (corner cell), then A, B
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
    });

    it('renders y-axis labels in the first column', () => {
      render(<HeatmapKpi data={sampleData} />);
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('renders values in data cells', () => {
      render(<HeatmapKpi data={sampleData} />);
      expect(screen.getByText('10.0')).toBeInTheDocument();
      expect(screen.getByText('20.0')).toBeInTheDocument();
      expect(screen.getByText('30.0')).toBeInTheDocument();
      expect(screen.getByText('40.0')).toBeInTheDocument();
    });
  });

  describe('null value handling', () => {
    it('displays em dash for cells with null value', () => {
      const data = [
        { x: 'A', y: '1', value: null },
        { x: 'A', y: '2', value: 5 },
      ];
      render(<HeatmapKpi data={data} />);
      expect(screen.getByText('—')).toBeInTheDocument();
      expect(screen.getByText('5.0')).toBeInTheDocument();
    });

    it('displays em dash for cells with undefined value', () => {
      const data = [
        { x: 'A', y: '1', value: undefined },
      ];
      render(<HeatmapKpi data={data} />);
      expect(screen.getByText('—')).toBeInTheDocument();
    });

    it('renders cell with gray background (e5e7eb) for null values', () => {
      const data = [{ x: 'A', y: '1', value: null }];
      const { container } = render(<HeatmapKpi data={data} />);
      // First data cell in tbody (skip y-label column)
      const dataCell = container.querySelector('tbody tr td:last-child');
      expect(dataCell).toBeInTheDocument();
      expect(dataCell.style.background).toBe('rgb(229, 231, 235)');
      expect(dataCell.style.color).toBe('rgb(156, 163, 175)');
    });
  });

  describe('color coding', () => {
    it('uses green when all values are equal (max === min)', () => {
      const data = [
        { x: 'A', y: '1', value: 50 },
        { x: 'A', y: '2', value: 50 },
      ];
      const { container } = render(<HeatmapKpi data={data} />);
      // Select only data cells (second column in each tbody row)
      const dataCells = container.querySelectorAll('tbody tr td:last-child');
      expect(dataCells.length).toBe(2);
      dataCells.forEach((td) => {
        expect(td.style.background).toBe('rgb(34, 197, 94)');
      });
    });

    it('produces different colors for different values', () => {
      const data = [
        { x: 'A', y: '1', value: 10 },
        { x: 'B', y: '1', value: 100 },
      ];
      const { container } = render(<HeatmapKpi data={data} />);
      const dataCells = container.querySelectorAll('tbody tr td:last-child');
      expect(dataCells.length).toBe(1); // only 1 row
      // With 1 row, we have 2 data cells (for A and B)
      const allDataCells = container.querySelectorAll('tbody td:not(:first-child)');
      expect(allDataCells.length).toBe(2);
      expect(allDataCells[0].style.background).not.toBe(allDataCells[1].style.background);
    });

    it('handles single unique value correctly (max === min)', () => {
      const data = [{ x: 'A', y: '1', value: 42 }];
      const { container } = render(<HeatmapKpi data={data} />);
      // Select only the data cell (not the y-label cell)
      const dataCell = container.querySelector('tbody tr td:last-child');
      expect(dataCell).toBeInTheDocument();
      expect(dataCell.style.background).toBe('rgb(34, 197, 94)');
    });
  });

  describe('sorting', () => {
    it('sorts x labels alphabetically', () => {
      const data = [
        { x: 'Z', y: '1', value: 1 },
        { x: 'A', y: '1', value: 2 },
        { x: 'M', y: '1', value: 3 },
      ];
      const { container } = render(<HeatmapKpi data={data} />);
      const ths = container.querySelectorAll('thead th');
      // First th is blank corner
      expect(ths[1].textContent).toBe('A');
      expect(ths[2].textContent).toBe('M');
      expect(ths[3].textContent).toBe('Z');
    });

    it('sorts y labels alphabetically', () => {
      const data = [
        { x: 'A', y: 'Z', value: 1 },
        { x: 'A', y: 'A', value: 2 },
        { x: 'A', y: 'M', value: 3 },
      ];
      const { container } = render(<HeatmapKpi data={data} />);
      const rows = container.querySelectorAll('tbody tr');
      expect(rows[0].querySelector('td').textContent).toBe('A');
      expect(rows[1].querySelector('td').textContent).toBe('M');
      expect(rows[2].querySelector('td').textContent).toBe('Z');
    });
  });

  describe('single row / column', () => {
    it('renders correctly with single data point', () => {
      const data = [{ x: 'A', y: '1', value: 99 }];
      const { container } = render(<HeatmapKpi data={data} />);
      expect(container.querySelector('table')).toBeInTheDocument();
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('99.0')).toBeInTheDocument();
    });
  });
});
