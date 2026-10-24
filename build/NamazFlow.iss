; NamazFlow user-level setup, compiled using Inno Setup 6
#define AppName "NamazFlow"
#define AppVersion "0.2.0"

[Setup]
AppId={{E0DBE342-B6AF-4BEA-8306-D5A02EF69587}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\NamazFlow
DefaultGroupName=NamazFlow
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=NamazFlow-0.2.0-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\NamazFlow.exe

[Files]
Source: "..\dist\NamazFlow.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NamazFlow"; Filename: "{app}\NamazFlow.exe"
Name: "{userdesktop}\NamazFlow"; Filename: "{app}\NamazFlow.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung"; Flags: unchecked

[Run]
Filename: "{app}\NamazFlow.exe"; Description: "NamazFlow starten"; Flags: postinstall nowait skipifsilent
