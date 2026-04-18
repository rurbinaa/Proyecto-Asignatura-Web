import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

/**
 * Hook para proteger rutas según el rol del usuario.
 * @param {string[]} allowedRoles - Lista de roles permitidos
 * @returns {function} - Componente wrapper
 */
export function withRoleProtection(Component, allowedRoles = []) {
  return function RoleProtectedWrapper(props) {
    const { user, loading } = useAuth();

    if (loading) return null;
    if (!user || (allowedRoles.length > 0 && !allowedRoles.includes(user.role))) {
      return <Navigate to="/" replace />;
    }
    return <Component {...props} />;
  };
}
