Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Jon\Programs\whisper-writer"
WshShell.Run """C:\Users\Jon\Programs\whisper-writer\.venv\Scripts\pythonw.exe"" ""C:\Users\Jon\Programs\whisper-writer\run.py""", 0, False
