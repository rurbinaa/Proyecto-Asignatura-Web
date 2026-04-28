import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Navbar from './Navbar';

describe('Navbar', () => {
  it('renders the user email when provided', () => {
    render(<Navbar user={{ email: 'test@example.com' }} />);
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('renders the navbar class', () => {
    const { container } = render(<Navbar user={{ email: 'test@test.com' }} />);
    expect(container.querySelector('.navbar')).toBeInTheDocument();
  });

  it('shows "User" fallback text when user email is not provided', () => {
    render(<Navbar user={{}} />);
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('shows "User" fallback text when user is null', () => {
    render(<Navbar user={null} />);
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('shows "User" fallback text when user is undefined', () => {
    render(<Navbar />);
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('renders the User icon from lucide-react', () => {
    const { container } = render(<Navbar user={{ email: 'a@b.com' }} />);
    // lucide-react renders inline SVGs
    const iconContainer = container.querySelector('.navbar-user-icon');
    expect(iconContainer).toBeInTheDocument();
  });

  it('renders the navbar-user container', () => {
    const { container } = render(<Navbar user={{ email: 'a@b.com' }} />);
    expect(container.querySelector('.navbar-user')).toBeInTheDocument();
  });

  it('renders navbar-email with the correct class', () => {
    const { container } = render(<Navbar user={{ email: 'test@test.com' }} />);
    expect(container.querySelector('.navbar-email')).toHaveTextContent('test@test.com');
  });
});
