Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strScriptPath
WshShell.Run "pythonw """ & strScriptPath & "\src\gui\lightweight_manager.py""", 0, False
