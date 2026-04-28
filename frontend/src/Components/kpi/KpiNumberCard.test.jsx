import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiNumberCard from './KpiNumberCard';

describe('KpiNumberCard', () => {
  it('renders the value formatted to 2 decimal places', () => {
    render(<KpiNumberCard value={42.1234} />);
    expect(screen.getByText('42.12')).toBeInTheDocument();
  });

  it('renders the label when provided', () => {
    render(<KpiNumberCard value={100} label="Total Units" />);
    expect(screen.getByText('Total Units')).toBeInTheDocument();
  });

  it('does not render a label when not provided', () => {
    render(<KpiNumberCard value={50} />);
    expect(screen.getByText('50.00')).toBeInTheDocument();
    expect(screen.queryByText('label')).not.toBeInTheDocument();
  });

  it('renders the unit suffix next to the value', () => {
    render(<KpiNumberCard value={75} unit="%" />);
    const valueElement = screen.getByText('75.00');
    expect(valueElement).toBeInTheDocument();
    expect(screen.getByText('%')).toBeInTheDocument();
  });

  it('does not render unit when not provided', () => {
    render(<KpiNumberCard value={30} />);
    expect(screen.getByText('30.00')).toBeInTheDocument();
    expect(screen.queryByText('%')).not.toBeInTheDocument();
  });

  it('renders the title when provided', () => {
    render(<KpiNumberCard value={88} title="Completion Rate" />);
    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
  });

  it('does not render title when not provided', () => {
    const { container } = render(<KpiNumberCard value={88} />);
    expect(container.querySelector('h3')).not.toBeInTheDocument();
  });

  it('displays em dash for non-finite values', () => {
    render(<KpiNumberCard value={NaN} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('displays em dash for null value', () => {
    render(<KpiNumberCard value={null} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('displays em dash for undefined value', () => {
    render(<KpiNumberCard value={undefined} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('displays em dash for Infinity', () => {
    render(<KpiNumberCard value={Infinity} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('renders with white background and rounded corners', () => {
    const { container } = render(<KpiNumberCard value={10} />);
    const wrapper = container.firstChild;
    expect(wrapper).toBeInTheDocument();
  });

  it('renders with unit and label together', () => {
    render(<KpiNumberCard value={99.9} unit="°C" label="Temperature" />);
    expect(screen.getByText('99.90')).toBeInTheDocument();
    expect(screen.getByText('°C')).toBeInTheDocument();
    expect(screen.getByText('Temperature')).toBeInTheDocument();
  });
});
