import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LoginView from '../views/LoginView';

describe('LoginView', () => {
  describe('Role Assignment Logic', () => {
    it('should assign manager role for gerente email', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'gerente@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'gerente@uniwell.com',
        role: 'manager',
      });
    });

    it('should assign manager role for gerencia email', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'gerencia@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'gerencia@uniwell.com',
        role: 'manager',
      });
    });

    it('should assign manager role for manager email', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'manager@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'manager@uniwell.com',
        role: 'manager',
      });
    });

    it('should assign manager role for admin email', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'admin@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'admin@uniwell.com',
        role: 'manager',
      });
    });

    it('should assign operator role for operator email', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'operator@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'operator@uniwell.com',
        role: 'operator',
      });
    });

    it('should assign manager role case-insensitively for GERENCIA', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'GERENCIA@uniwell.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(onLogin).toHaveBeenCalledWith({
        email: 'GERENCIA@uniwell.com',
        role: 'manager',
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error message for empty fields', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
      expect(onLogin).not.toHaveBeenCalled();
    });

    it('should show error message for empty email only', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText('••••••••'), {
        target: { value: 'password123' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
      expect(onLogin).not.toHaveBeenCalled();
    });

    it('should show error message for empty password only', () => {
      const onLogin = vi.fn();
      render(<LoginView onLogin={onLogin} />);

      fireEvent.change(screen.getByPlaceholderText(/ej. gerente@uniwell.com/i), {
        target: { value: 'gerente@uniwell.com' },
      });
      fireEvent.submit(screen.getByRole('button', { name: /log in/i }));

      expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
      expect(onLogin).not.toHaveBeenCalled();
    });
  });
});
