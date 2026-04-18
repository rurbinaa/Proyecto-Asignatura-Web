import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginView from '../views/LoginView';
import { useAuth } from '../contexts/AuthContext';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('LoginView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Authentication Flow', () => {
    it('should call the login function from context with correct credentials', async () => {
      const mockLogin = vi.fn().mockResolvedValue(true);
      useAuth.mockReturnValue({ login: mockLogin });

      render(<LoginView />);

      fireEvent.change(screen.getByPlaceholderText('e.g. operator_01'), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error message for empty fields', () => {
      useAuth.mockReturnValue({ login: vi.fn() });
      render(<LoginView />);

      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
    });

    it('should show an error message when credentials are invalid', async () => {
      const mockLogin = vi.fn().mockResolvedValue(false);
      useAuth.mockReturnValue({ login: mockLogin });

      render(<LoginView />);

      fireEvent.change(screen.getByPlaceholderText('e.g. operator_01'), { target: { value: 'wronguser' } });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'wrongpass' } });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials or server error.')).toBeInTheDocument();
      });
    });

    it('should show an error message when the backend is offline', async () => {
      const mockLogin = vi.fn().mockRejectedValue(new Error('Network Error'));
      useAuth.mockReturnValue({ login: mockLogin });

      render(<LoginView />);

      fireEvent.change(screen.getByPlaceholderText('e.g. operator_01'), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByText('Connection error. Please try again later.')).toBeInTheDocument();
      });
    });
  });

  describe('UI States', () => {
    it('should change button text to Authenticating while loading', async () => {
      let resolveLogin;
      const mockPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      const mockLogin = vi.fn().mockReturnValue(mockPromise);
      useAuth.mockReturnValue({ login: mockLogin });

      render(<LoginView />);

      fireEvent.change(screen.getByPlaceholderText('e.g. operator_01'), { target: { value: 'testuser' } });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } });
      
      const button = screen.getByRole('button', { name: /log in/i });
      fireEvent.submit(button);

      expect(button).toHaveTextContent('Authenticating...');

      resolveLogin(true);
    });
  });
});