'------------------------------
' Deus seja Louvado!
' Acesso MariaDB via DAL.py (PROJ_ONIX / banco crip)
'------------------------------

Imports System.Data
Imports System.Diagnostics
Imports System.IO
Imports Newtonsoft.Json.Linq

Public Class ClDAL

    Private Shared Function ProjectRoot() As String
        Dim dir As DirectoryInfo = New DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory)
        Do While dir IsNot Nothing
            If Directory.Exists(Path.Combine(dir.FullName, "scripts")) AndAlso
               Directory.Exists(Path.Combine(dir.FullName, "DAL")) Then
                Return dir.FullName
            End If
            dir = dir.Parent
        Loop
        Throw New DirectoryNotFoundException("Raiz PROJ_ONIX não encontrada (scripts/DAL).")
    End Function

    Private Shared Function RunBridge(command As String, sql As String) As String
        Dim root = ProjectRoot()
        Dim bridge = Path.Combine(root, "scripts", "dal_bridge.py")
        If Not File.Exists(bridge) Then
            Throw New FileNotFoundException("dal_bridge.py não encontrado.", bridge)
        End If

        Dim psi As New ProcessStartInfo() With {
            .FileName = "py",
            .Arguments = $"-3 ""{bridge}"" {command}",
            .WorkingDirectory = root,
            .UseShellExecute = False,
            .RedirectStandardInput = True,
            .RedirectStandardOutput = True,
            .RedirectStandardError = True,
            .CreateNoWindow = True
        }

        Using proc As Process = Process.Start(psi)
            proc.StandardInput.Write(sql)
            proc.StandardInput.Close()
            Dim output = proc.StandardOutput.ReadToEnd()
            Dim err = proc.StandardError.ReadToEnd()
            proc.WaitForExit()
            If proc.ExitCode <> 0 AndAlso String.IsNullOrWhiteSpace(output) Then
                Throw New ApplicationException("DAL bridge: " & err)
            End If
            Return output
        End Using
    End Function

    Public Function ReadDataTable(sql As String) As DataTable
        Dim payload = JObject.Parse(RunBridge("read", sql))
        If payload.Value(Of Boolean?)("ok") <> True Then
            Throw New ApplicationException(payload.Value(Of String)("error"))
        End If

        Dim dt As New DataTable()
        Dim cols = payload("columns")
        Dim rows = payload("rows")
        If cols Is Nothing OrElse cols.Type <> JTokenType.Array Then Return dt

        For Each col In cols
            dt.Columns.Add(col.ToString(), GetType(String))
        Next
        If rows Is Nothing OrElse rows.Type <> JTokenType.Array Then Return dt

        For Each item As JObject In rows
            Dim row = dt.NewRow()
            For Each prop In item.Properties()
                row(prop.Name) = If(prop.Value.Type = JTokenType.Null, DBNull.Value, prop.Value.ToString())
            Next
            dt.Rows.Add(row)
        Next
        Return dt
    End Function

    Public Sub Create(sql As String)
        ExecuteCommand("create", sql)
    End Sub

    Public Sub Update(sql As String)
        ExecuteCommand("update", sql)
    End Sub

    Public Sub Delete(sql As String)
        ExecuteCommand("delete", sql)
    End Sub

    Private Shared Sub ExecuteCommand(command As String, sql As String)
        Dim payload = JObject.Parse(RunBridge(command, sql))
        If payload.Value(Of Boolean?)("ok") <> True Then
            Throw New ApplicationException(payload.Value(Of String)("error"))
        End If
    End Sub

End Class
