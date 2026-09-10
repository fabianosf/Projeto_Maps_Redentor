import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider } from '@/context/AuthContext';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { PrimeiroAcessoScreen } from '@/screens/auth/PrimeiroAcessoScreen';
import { UsuariosScreen } from '@/screens/admin/UsuariosScreen';
import { MapasListScreen } from '@/screens/mapa/MapasListScreen';
import { MapaDetalheScreen } from '@/screens/mapa/MapaDetalheScreen';
import { MapaFormScreen } from '@/screens/mapa/MapaFormScreen';
import { ConfiguracaoScreen } from '@/screens/principal/ConfiguracaoScreen';
import { EntradaSaidaScreen } from '@/screens/principal/EntradaSaidaScreen';
import { GuiaScreen } from '@/screens/principal/GuiaScreen';
import { NovaGuiaScreen } from '@/screens/principal/NovaGuiaScreen';
import { IndicadoresConfigScreen } from '@/screens/principal/IndicadoresConfigScreen';
import { IndicadoresScreen } from '@/screens/principal/IndicadoresScreen';
import { BancoHorasScreen } from '@/screens/principal/BancoHorasScreen';
import { TelaPrincipalScreen } from '@/screens/principal/TelaPrincipalScreen';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/primeiro-acesso" element={<PrimeiroAcessoScreen />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/principal" element={<TelaPrincipalScreen />} />
          <Route path="/usuarios" element={<UsuariosScreen />} />
          <Route path="/guia" element={<GuiaScreen />} />
          <Route path="/guia/nova" element={<NovaGuiaScreen />} />
          <Route path="/entrada-saida" element={<EntradaSaidaScreen />} />
          <Route path="/configuracao" element={<ConfiguracaoScreen />} />
          <Route
            path="/configuracao/indicadores"
            element={<IndicadoresConfigScreen />}
          />
          <Route path="/indicadores" element={<IndicadoresScreen />} />
          <Route path="/banco-horas" element={<BancoHorasScreen />} />
          <Route path="/mapas" element={<MapasListScreen />} />
          <Route path="/mapas/novo" element={<MapaFormScreen />} />
          <Route path="/mapas/:id/editar" element={<MapaFormScreen />} />
          <Route path="/mapas/:id" element={<MapaDetalheScreen />} />
        </Route>

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
      <Toaster position="top-center" richColors closeButton />
    </AuthProvider>
  );
}
