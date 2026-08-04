import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { UsuariosScreen } from '@/screens/admin/UsuariosScreen';
import { CadastroSenhaScreen } from '@/screens/auth/CadastroSenhaScreen';
import { LoginScreen } from '@/screens/auth/LoginScreen';
import { CadastroRegistroScreen } from '@/screens/mapa/CadastroRegistroScreen';
import { CadastroViagemScreen } from '@/screens/mapa/CadastroViagemScreen';
import { ListaMapaScreen } from '@/screens/mapa/ListaMapaScreen';
import { MapaScreen } from '@/screens/mapa/MapaScreen';
import { MapasScreen } from '@/screens/mapa/MapasScreen';
import { RegistrosMapaScreen } from '@/screens/mapa/RegistrosMapaScreen';
import { ViagensScreen } from '@/screens/mapa/ViagensScreen';
import { ConfiguracaoScreen } from '@/screens/principal/ConfiguracaoScreen';
import { TelaPrincipalScreen } from '@/screens/principal/TelaPrincipalScreen';

export default function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<LoginScreen />} />
        <Route path="/cadastro-senha" element={<CadastroSenhaScreen />} />
        <Route path="/principal" element={<TelaPrincipalScreen />} />
        <Route path="/configuracao" element={<ConfiguracaoScreen />} />
        <Route path="/cadastro-usuario" element={<UsuariosScreen />} />
        <Route path="/lista-mapa" element={<ListaMapaScreen />} />
        {/* Botão + da lista → Tela de Mapas (formulário) */}
        <Route path="/mapas" element={<MapasScreen />} />
        <Route path="/mapas/:idRegistro" element={<MapasScreen />} />
        {/* Tela 06 — Registros */}
        <Route path="/mapas/:idRegistro/registros" element={<RegistrosMapaScreen />} />
        <Route path="/mapas/:idRegistro/registros/novo" element={<CadastroRegistroScreen />} />
        {/* Tela VIAGEM / Cadastrar_Viagem (rotas mais específicas antes de :idItem) */}
        <Route
          path="/mapas/:idRegistro/registros/:idItem/viagens"
          element={<ViagensScreen />}
        />
        <Route
          path="/mapas/:idRegistro/registros/:idItem/viagens/novo"
          element={<CadastroViagemScreen />}
        />
        <Route
          path="/mapas/:idRegistro/registros/:idItem/viagens/:idViagem"
          element={<CadastroViagemScreen />}
        />
        {/* Tela 07 — Cadastro de Registro */}
        <Route
          path="/mapas/:idRegistro/registros/:idItem"
          element={<CadastroRegistroScreen />}
        />
        {/* Compatibilidade com rotas antigas */}
        <Route path="/cad-mapa" element={<Navigate to="/mapas" replace />} />
        <Route path="/cad-mapa/:idRegistro" element={<MapasScreen />} />
        <Route path="/mapa/:idRegistro" element={<MapaScreen />} />
        <Route path="/mapa" element={<Navigate to="/lista-mapa" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster position="top-center" richColors closeButton />
    </div>
  );
}
