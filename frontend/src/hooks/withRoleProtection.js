import { useAuth } from '../contexts/AuthContext';

/**
 * Hook (HOC) para proteger rutas según el rol del usuario.
 * @param {Component} Component - Componente a proteger
 * @param {string[]} allowedRoles - Lista de roles permitidos
 * @returns {function} - Componente wrapper
 */
export function withRoleProtection(Component, allowedRoles = []) {
  return function RoleProtectedWrapper(props) {
    const { user, loading } = useAuth();

    if (loading) return null;

    if (!user || (allowedRoles.length > 0 && !allowedRoles.includes(user.role))) {
      localStorage.removeItem('rift-activeView');
      window.location.replace('/'); 
      return null;
    }

    return <Component {...props} />;
  };
}