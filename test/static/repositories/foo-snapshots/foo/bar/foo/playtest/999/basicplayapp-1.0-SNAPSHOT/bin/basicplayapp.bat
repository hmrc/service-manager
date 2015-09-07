@REM basicplayapp launcher script
@REM
@REM Envioronment:
@REM JAVA_HOME - location of a JDK home dir (optional if java on path)
@REM CFG_OPTS  - JVM options (optional)
@REM Configuration:
@REM BASICPLAYAPP_config.txt found in the BASICPLAYAPP_HOME.
@setlocal enabledelayedexpansion

@echo off
if "%BASICPLAYAPP_HOME%"=="" set "BASICPLAYAPP_HOME=%~dp0\\.."
set ERROR_CODE=0

set "APP_LIB_DIR=%BASICPLAYAPP_HOME%\lib\"

rem Detect if we were double clicked, although theoretically A user could
rem manually run cmd /c
for %%x in (%cmdcmdline%) do if %%~x==/c set DOUBLECLICKED=1

rem FIRST we load the config file of extra options.
set "CFG_FILE=%BASICPLAYAPP_HOME%\BASICPLAYAPP_config.txt"
set CFG_OPTS=
if exist %CFG_FILE% (
  FOR /F "tokens=* eol=# usebackq delims=" %%i IN ("%CFG_FILE%") DO (
    set DO_NOT_REUSE_ME=%%i
    rem ZOMG (Part #2) WE use !! here to delay the expansion of
    rem CFG_OPTS, otherwise it remains "" for this loop.
    set CFG_OPTS=!CFG_OPTS! !DO_NOT_REUSE_ME!
  )
)

rem We use the value of the JAVACMD environment variable if defined
set _JAVACMD=%JAVACMD%

if "%_JAVACMD%"=="" (
  if not "%JAVA_HOME%"=="" (
    if exist "%JAVA_HOME%\bin\java.exe" set "_JAVACMD=%JAVA_HOME%\bin\java.exe"
  )
)

if "%_JAVACMD%"=="" set _JAVACMD=java

rem Detect if this java is ok to use.
for /F %%j in ('"%_JAVACMD%" -version  2^>^&1') do (
  if %%~j==Java set JAVAINSTALLED=1
)

rem Detect the same thing about javac
if "%_JAVACCMD%"=="" (
  if not "%JAVA_HOME%"=="" (
    if exist "%JAVA_HOME%\bin\javac.exe" set "_JAVACCMD=%JAVA_HOME%\bin\javac.exe"
  )
)
if "%_JAVACCMD%"=="" set _JAVACCMD=javac
for /F %%j in ('"%_JAVACCMD%" -version 2^>^&1') do (
  if %%~j==javac set JAVACINSTALLED=1
)

rem BAT has no logical or, so we do it OLD SCHOOL! Oppan Redmond Style
set JAVAOK=true
if not defined JAVAINSTALLED set JAVAOK=false
rem TODO - JAVAC is an optional requirement.
if not defined JAVACINSTALLED set JAVAOK=false

if "%JAVAOK%"=="false" (
  echo.
  echo A Java JDK is not installed or can't be found.
  if not "%JAVA_HOME%"=="" (
    echo JAVA_HOME = "%JAVA_HOME%"
  )
  echo.
  echo Please go to
  echo   http://www.oracle.com/technetwork/java/javase/downloads/index.html
  echo and download a valid Java JDK and install before running basicplayapp.
  echo.
  echo If you think this message is in error, please check
  echo your environment variables to see if "java.exe" and "javac.exe" are
  echo available via JAVA_HOME or PATH.
  echo.
  if defined DOUBLECLICKED pause
  exit /B 1
)


rem We use the value of the JAVA_OPTS environment variable if defined, rather than the config.
set _JAVA_OPTS=%JAVA_OPTS%
if "%_JAVA_OPTS%"=="" set _JAVA_OPTS=%CFG_OPTS%

:run
 
set "APP_CLASSPATH=%APP_LIB_DIR%\default.basicplayapp-1.0-SNAPSHOT.jar;%APP_LIB_DIR%\org.scala-lang.scala-library-2.10.3.jar;%APP_LIB_DIR%\com.typesafe.play.play-jdbc_2.10-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.play_2.10-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.sbt-link-2.2.2.jar;%APP_LIB_DIR%\org.javassist.javassist-3.18.0-GA.jar;%APP_LIB_DIR%\com.typesafe.play.play-exceptions-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.templates_2.10-2.2.2.jar;%APP_LIB_DIR%\com.github.scala-incubator.io.scala-io-file_2.10-0.4.2.jar;%APP_LIB_DIR%\com.github.scala-incubator.io.scala-io-core_2.10-0.4.2.jar;%APP_LIB_DIR%\com.jsuereth.scala-arm_2.10-1.3.jar;%APP_LIB_DIR%\com.typesafe.play.play-iteratees_2.10-2.2.2.jar;%APP_LIB_DIR%\org.scala-stm.scala-stm_2.10-0.7.jar;%APP_LIB_DIR%\com.typesafe.config-1.0.2.jar;%APP_LIB_DIR%\com.typesafe.play.play-json_2.10-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.play-functional_2.10-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.play-datacommons_2.10-2.2.2.jar;%APP_LIB_DIR%\joda-time.joda-time-2.2.jar;%APP_LIB_DIR%\org.joda.joda-convert-1.3.1.jar;%APP_LIB_DIR%\com.fasterxml.jackson.core.jackson-annotations-2.2.2.jar;%APP_LIB_DIR%\com.fasterxml.jackson.core.jackson-core-2.2.2.jar;%APP_LIB_DIR%\com.fasterxml.jackson.core.jackson-databind-2.2.2.jar;%APP_LIB_DIR%\org.scala-lang.scala-reflect-2.10.3.jar;%APP_LIB_DIR%\io.netty.netty-3.7.0.Final.jar;%APP_LIB_DIR%\com.typesafe.netty.netty-http-pipelining-1.1.2.jar;%APP_LIB_DIR%\org.slf4j.slf4j-api-1.7.5.jar;%APP_LIB_DIR%\org.slf4j.jul-to-slf4j-1.7.5.jar;%APP_LIB_DIR%\org.slf4j.jcl-over-slf4j-1.7.5.jar;%APP_LIB_DIR%\ch.qos.logback.logback-core-1.0.13.jar;%APP_LIB_DIR%\ch.qos.logback.logback-classic-1.0.13.jar;%APP_LIB_DIR%\com.typesafe.akka.akka-actor_2.10-2.2.0.jar;%APP_LIB_DIR%\com.typesafe.akka.akka-slf4j_2.10-2.2.0.jar;%APP_LIB_DIR%\org.apache.commons.commons-lang3-3.1.jar;%APP_LIB_DIR%\com.ning.async-http-client-1.7.18.jar;%APP_LIB_DIR%\oauth.signpost.signpost-core-1.2.1.2.jar;%APP_LIB_DIR%\commons-codec.commons-codec-1.3.jar;%APP_LIB_DIR%\oauth.signpost.signpost-commonshttp4-1.2.1.2.jar;%APP_LIB_DIR%\org.apache.httpcomponents.httpcore-4.0.1.jar;%APP_LIB_DIR%\org.apache.httpcomponents.httpclient-4.0.1.jar;%APP_LIB_DIR%\commons-logging.commons-logging-1.1.1.jar;%APP_LIB_DIR%\xerces.xercesImpl-2.11.0.jar;%APP_LIB_DIR%\xml-apis.xml-apis-1.4.01.jar;%APP_LIB_DIR%\javax.transaction.jta-1.1.jar;%APP_LIB_DIR%\com.jolbox.bonecp-0.8.0.RELEASE.jar;%APP_LIB_DIR%\com.google.guava.guava-14.0.1.jar;%APP_LIB_DIR%\com.h2database.h2-1.3.172.jar;%APP_LIB_DIR%\tyrex.tyrex-1.0.1.jar;%APP_LIB_DIR%\com.typesafe.play.anorm_2.10-2.2.2.jar;%APP_LIB_DIR%\com.typesafe.play.play-cache_2.10-2.2.2.jar;%APP_LIB_DIR%\net.sf.ehcache.ehcache-core-2.6.6.jar"
set "APP_MAIN_CLASS=play.core.server.NettyServer"

rem TODO - figure out how to pass arguments....
"%_JAVACMD%" %_JAVA_OPTS% %BASICPLAYAPP_OPTS% -cp "%APP_CLASSPATH%" %APP_MAIN_CLASS% %CMDS%
if ERRORLEVEL 1 goto error
goto end

:error
set ERROR_CODE=1

:end

@endlocal

exit /B %ERROR_CODE%
