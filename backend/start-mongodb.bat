@echo off
echo Starting MongoDB Server...
echo.

REM Try common MongoDB installation paths
set MONGOD_PATH=

if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" (
    set MONGOD_PATH=C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe
) else if exist "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" (
    set MONGOD_PATH=C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe
) else if exist "C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe" (
    set MONGOD_PATH=C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe
) else if exist "C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe" (
    set MONGOD_PATH=C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe
)

if "%MONGOD_PATH%"=="" (
    echo ERROR: MongoDB server (mongod.exe) not found!
    echo.
    echo Please install MongoDB from: https://www.mongodb.com/try/download/community
    echo Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas
    pause
    exit /b 1
)

REM Create data directory if it doesn't exist
if not exist "C:\data\db" (
    echo Creating data directory C:\data\db...
    mkdir "C:\data\db"
)

echo Found MongoDB at: %MONGOD_PATH%
echo Data directory: C:\data\db
echo.
echo Starting MongoDB server on port 27017...
echo Press Ctrl+C to stop
echo.

"%MONGOD_PATH%" --dbpath "C:\data\db"
