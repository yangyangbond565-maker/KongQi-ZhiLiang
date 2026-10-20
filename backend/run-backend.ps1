# 启动后端：先读取 .env.local 中的数据库口令，再运行 jar
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root '.env.local'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}
$jar = Join-Path $root 'aqp-server\target\aqp-server-1.0.0.jar'
if (-not (Test-Path $jar)) { Write-Error "未找到 jar，请先在 backend 目录执行 mvn -DskipTests package"; exit 1 }
Write-Host "启动 aqp-server ..."
java -jar $jar
