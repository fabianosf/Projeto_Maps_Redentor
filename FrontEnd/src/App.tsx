import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider } from '@/context/AuthContext';
import { MainTabLayout } from '@/layouts/MainTabLayout';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { PrimeiroAcessoScreen } from '@/screens/auth/PrimeiroAcessoScreen';
import { RecuperarSenhaScreen } from '@/screens/auth/RecuperarSenhaScreen';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/primeiro-acesso" element={<PrimeiroAcessoScreen />} />
        <Route path="/recuperar-senha" element={<RecuperarSenhaScreen />} />

        <Route element={<ProtectedRoute />}>
          <Route path="*" element={<MainTabLayout />} />
        </Route>

        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
      <Toaster position="top-center" richColors closeButton />
    </AuthProvider>
  );
}
