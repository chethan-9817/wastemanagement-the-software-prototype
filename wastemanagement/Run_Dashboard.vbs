Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python -m streamlit run """ & currentDir & "\app.py""", 0, False
Set WshShell = Nothing
