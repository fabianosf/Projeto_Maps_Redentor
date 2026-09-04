# Integração PROJ_ONIX com DAL (MariaDB / banco `crip`)

## Situação

Integração instalada em **`C:\PROJ_ONIX`** (ago/2026).

- Junction `C:\PROJ_ONIX\DAL` → `PROJ_MAP\DAL` (mesmo módulo DAL.py)
- `dal_factory.py` (config padrão: `crip.dat` / banco **crip**)
- `scripts/dal_bridge.py` (ponte VB.NET ↔ Python)
- `PROJ_ONIX/ClDAL.vb`
- `crip.dat` gerado em `DAL/arquivos_crip/arq/`
- Conexão testada: `mariadb://...@10.1.1.29:3306/crip`

Para reinstalar:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP\scripts\proj_onix_integration\instalar_dal_onix.ps1"
```

## 1. Liberar espaço em C:

Libere pelo menos **50–100 MB** em `C:` (Lixeira, `%TEMP%`, downloads, etc.).

## 2. Gerar `crip.dat` (uma vez, no PROJ_MAP)

```powershell
cd "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP"
py -3 scripts\gerar_configs_map.py
```

Isso cria `DAL/arquivos_crip/chave/chave.key` (se não existir) e `DAL/arquivos_crip/arq/crip.dat` apontando para `10.1.1.29:3306/crip`.

## 3. Instalar no PROJ_ONIX

PowerShell **como Administrador** (junction):

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& "E:\Trabalho\Projetos\Projetos Ativos\PROJ_MAP\scripts\proj_onix_integration\instalar_dal_onix.ps1
```

O script:
1. Cria `C:\PROJ_ONIX\DAL` como junction para `PROJ_MAP\DAL`
2. Copia `LOG`, `dal_factory.py`, `scripts/dal_bridge.py`, `ClDAL.vb`
3. Instala dependências Python (`pymysql`, `pandas`, `cryptography`)
4. Testa conexão com `crip`

## 4. Projeto VB.NET

Em `C:\PROJ_ONIX\PROJ_ONIX\PROJ_ONIX.vbproj`, adicione:

```xml
<ItemGroup>
  <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
</ItemGroup>
```

O SDK-style inclui automaticamente `ClDAL.vb` na pasta do projeto.

Compile:

```powershell
cd C:\PROJ_ONIX\PROJ_ONIX
dotnet build
```

## 5. Teste manual da ponte Python

```powershell
cd C:\PROJ_ONIX
echo "SELECT parametro, valor FROM tb_conf" | py -3 scripts\dal_bridge.py read
```

## Arquitetura

```
FrmMain.vb  →  ClDAL.vb  →  py dal_bridge.py  →  dal_factory  →  DAL.py  →  MariaDB crip
```

Variáveis de ambiente opcionais:
- `PROJ_ONIX_CONFIG=crip` (padrão)
- `PROJ_ONIX_SGBD=mariadb` (padrão)

## Tabelas SQL no FrmMain

O código VB ainda referencia tabelas legadas `snc_tb_*`. O banco `crip` usa `tb_*` (`tb_conf`, `tb_opor`, etc.).  
Após a infra DAL funcionar, será necessário **ajustar os SQL** em `FrmMain.vb` ou criar views `snc_tb_*` no MariaDB.

## Arquivos de referência (templates)

| Arquivo | Origem |
|---------|--------|
| `dal_factory.py` | `templates/dal_factory.py` |
| `scripts/dal_bridge.py` | `templates/scripts/dal_bridge.py` |
| `PROJ_ONIX/ClDAL.vb` | `templates/PROJ_ONIX/ClDAL.vb` |
