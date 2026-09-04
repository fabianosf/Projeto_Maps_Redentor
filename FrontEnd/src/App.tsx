import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { UsuariosScreen } from '@/screens/admin/UsuariosScreen';
import { CadastroSenhaScreen } from '@/screens/auth/CadastroSenhaScreen';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { ConfiguracaoScreen } from '@/screens/principal/ConfiguracaoScreen';
import { GuiaScreen } from '@/screens/principal/GuiaScreen';
import { IndicadoresScreen } from '@/screens/principal/IndicadoresScreen';
import { MensagemScreen } from '@/screens/principal/MensagemScreen';
import { EntradaSaidaScreen } from '@/screens/principal/EntradaSaidaScreen';
import { TelaPrincipalScreen } from '@/screens/principal/TelaPrincipalScreen';

/** Rotas alinhadas ao cap. 10 do ODT (10 telas). */
export default function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<LoginScreen />} />
        <Route path="/cadastro-senha" element={<CadastroSenhaScreen />} />
        <Route path="/cadastro-usuario" element={<UsuariosScreen />} />
        <Route path="/principal" element={<TelaPrincipalScreen />} />
        <Route path="/entrada-saida" element={<EntradaSaidaScreen />} />
        <Route path="/mensagem" element={<MensagemScreen />} />
        <Route path="/guia" element={<GuiaScreen />} />
        <Route path="/configuracao" element={<ConfiguracaoScreen />} />
        <Route path="/indicadores" element={<IndicadoresScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster position="top-center" richColors closeButton />
    </div>
  );
}
