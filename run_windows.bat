@echo off
setlocal
cd /d "%~dp0"
rem Prefer the default interpreter; try other installed versions if unsupported.
py -3 start.py --check >nul 2>&1
if not errorlevel 1 (
  py -3 start.py %*
  goto done
)
for %%V in (3.14 3.13 3.12 3.11 3.10 3.9) do (
  py -%%V start.py --check >nul 2>&1
  if not errorlevel 1 (
    py -%%V start.py %*
    goto done
  )
)
python start.py --check >nul 2>&1
if not errorlevel 1 (
  python start.py %*
  goto done
)
echo Compatible 64-bit Python 3.9-3.14 was not found. See README.txt.
:done
pause
endlocal
