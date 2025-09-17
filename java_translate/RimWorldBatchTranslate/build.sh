#!/bin/bash

echo "正在构建 RimWorldBatchTranslate..."

# 检查Maven是否安装
if ! command -v mvn &> /dev/null; then
    echo "错误：未找到Maven，请先安装Maven"
    echo "下载地址：https://maven.apache.org/download.cgi"
    exit 1
fi

# 清理并编译
echo "清理项目..."
mvn clean

echo "编译项目..."
mvn compile

echo "打包项目..."
mvn package

echo "构建完成！"
echo "可执行文件位置：target/rimworld-batch-translate-1.0.0-jar-with-dependencies.jar"
echo ""
echo "使用方法："
echo "java -jar target/rimworld-batch-translate-1.0.0-jar-with-dependencies.jar" 