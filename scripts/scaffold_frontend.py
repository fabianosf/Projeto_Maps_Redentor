# -*- coding: utf-8 -*-
"""Scaffold do app React Native (Expo) — RedMapa. Telas: aguardar implementação."""

from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FRONTEND = BASE / "FrontEnd"

FILES = {
    "package.json": """{
  "name": "redmapa-frontend",
  "version": "1.0.0",
  "private": true,
  "main": "index.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  },
  "dependencies": {
    "@react-navigation/native": "^7.0.14",
    "@react-navigation/native-stack": "^7.2.0",
    "expo": "~52.0.0",
    "expo-status-bar": "~2.0.0",
    "react": "18.3.1",
    "react-native": "0.76.3",
    "react-native-safe-area-context": "4.12.0",
    "react-native-screens": "~4.4.0"
  },
  "devDependencies": {
    "@babel/core": "^7.25.0",
    "@types/react": "~18.3.0",
    "typescript": "~5.3.0"
  }
}
""",
    "app.json": """{
  "expo": {
    "name": "RedMapa",
    "slug": "redmapa",
    "version": "1.0.0",
    "orientation": "portrait",
    "userInterfaceStyle": "light",
    "splash": {
      "backgroundColor": "#f5e6c8"
    },
    "ios": {
      "supportsTablet": false
    },
    "android": {
      "adaptiveIcon": {
        "backgroundColor": "#f5e6c8"
      }
    }
  }
}
""",
    "tsconfig.json": """{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["**/*.ts", "**/*.tsx"]
}
""",
    "babel.config.js": """module.exports = function (api) {
  api.cache(true);
  return { presets: ['babel-preset-expo'] };
};
""",
    "index.js": """import { registerRootComponent } from 'expo';
import App from './App';
registerRootComponent(App);
""",
    "App.tsx": """import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

/**
 * RedMapa — React Native (Doc_Proj_Map.odt).
 * Navegação e telas (RF-UI / RF-MAP-UI): implementação pendente.
 */
export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>RedMapa</Text>
      <Text style={styles.subtitle}>App mobile — estrutura inicial</Text>
      <StatusBar style="dark" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5e6c8',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: '#2c2416',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#5c4a32',
    textAlign: 'center',
  },
});
""",
    "src/config/api.ts": """/** API BackEnd Flask — Doc_Proj_Map.odt §4.6 */
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://10.0.2.2:5000/api/v1';
""",
    "src/config/constants.ts": """/** RF-RN-001 — perfis */
export const PERFIL_ADMIN = 1;
export const PERFIL_DESPACHANTE = 2;
export const SENHA_PROVISORIA = '12345';
""",
    "src/api/client.ts": """import { API_BASE_URL } from '../config/api';

export async function apiFetch(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  return { response, data };
}
""",
    "src/api/auth.ts": """import { apiFetch } from './client';

export function login(matricula: string, senha: string) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ matricula, senha }),
  });
}
""",
    "src/navigation/.gitkeep": "",
    "src/screens/.gitkeep": "",
    "src/types/index.ts": "export type CodigoPerfil = 1 | 2;\n",
    "src/utils/validation.ts": """/** RF-RN-007 */
const PASSWORD_POLICY =
  /^(?=.*[A-Za-z])(?=.*\\d)(?=.*[!@#$%^&*(),.?\":{}|<>_\\-+=\\[\\]\\\\;/`~]).{8,}$/;

export function validatePassword(nova: string, confirmacao: string): string | null {
  if (nova !== confirmacao) return 'Senhas digitadas diferentes!';
  if (!PASSWORD_POLICY.test(nova)) return 'Senha inválida!';
  return null;
}
""",
    ".gitignore": "node_modules/\n.expo/\ndist/\n",
}


def main() -> None:
    for rel, content in FILES.items():
        path = FRONTEND / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"  + FrontEnd/{rel}")


if __name__ == "__main__":
    print(f"Scaffold React Native em {FRONTEND}")
    main()
