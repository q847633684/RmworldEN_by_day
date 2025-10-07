package com.daytranslation;

import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.profile.DefaultProfile;
import org.apache.commons.csv.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.regex.*;
import java.util.Scanner;

public class RimWorldBatchTranslate {
    // 常量定义
    private static final Long DEFAULT_MODEL_ID = 27345L;
    private static final int DEFAULT_MAX_RETRY = 3;
    private static final long TRANSLATION_DELAY_MS = 500L;
    private static final long RETRY_DELAY_MS = 2000L;
    private static final String ALIMT_OPEN_TAG = "<ALIMT >";
    private static final String ALIMT_CLOSE_TAG = "</ALIMT>";

    static String accessKeyId = null;
    static String accessKeySecret = null;
    static Long modelId = DEFAULT_MODEL_ID;

    /**
     * 判断是否应该跳过翻译
     * 
     * @param key  键值
     * @param text 文本内容
     * @return 跳过原因，如果不跳过则返回null
     */
    private static String shouldSkipTranslation(String key, String text) {
        // 检查空值
        if (key == null || text == null || key.trim().isEmpty() || text.trim().isEmpty()) {
            return "空内容";
        }

        String trimmedText = text.trim();

        // 1. 纯数字
        if (trimmedText.matches("^\\d+$")) {
            return "纯数字";
        }

        // 2. 纯空格或制表符
        if (trimmedText.matches("^\\s+$")) {
            return "纯空白字符";
        }

        // 3. ALIMT标签检查
        // 检查是否只包含ALIMT标签（没有其他内容）
        // 先移除所有ALIMT标签，然后检查剩余内容
        String withoutAlimt = trimmedText.replaceAll("<ALIMT >.*?</ALIMT>", "").trim();
        if (withoutAlimt.isEmpty() && trimmedText.contains("<ALIMT >")) {
            // 如果移除ALIMT标签后为空，且原文本包含ALIMT标签
            if (trimmedText.matches("^<ALIMT >.*</ALIMT>$")) {
                return "纯ALIMT保护内容";
            } else {
                return "多个ALIMT标签";
            }
        }

        // 4. 文件路径或URL
        if (trimmedText.matches("^[a-zA-Z]:\\\\") || // Windows路径
                trimmedText.matches("^/") || // Unix路径
                trimmedText.matches("^https?://")) { // URL
            return "路径或URL";
        }

        // 5. 布尔值
        if (trimmedText.matches("^(true|false)$")) {
            return "布尔值";
        }

        // 6. 浮点数
        if (trimmedText.matches("^-?\\d+\\.\\d+$")) {
            return "浮点数";
        }

        // 7. 十六进制数
        if (trimmedText.matches("^0x[0-9a-fA-F]+$")) {
            return "十六进制数";
        }
        // 不跳过
        return null;
    }

    /**
     * 移除ALIMT标签，只保留标签内的内容
     * 
     * @param text 包含ALIMT标签的文本
     * @return 移除标签后的文本
     */
    private static String removeAlimtTags(String text) {
        if (text == null || text.trim().isEmpty()) {
            return text;
        }

        // 移除所有 <ALIMT > 和 </ALIMT> 标签
        String result = text.replaceAll(ALIMT_OPEN_TAG, "").replaceAll(ALIMT_CLOSE_TAG, "");

        return result;
    }

    public static void main(String[] args) throws Exception {
        Scanner scanner = new Scanner(System.in, StandardCharsets.UTF_8);

        // 检查是否是交互模式（通过环境变量或参数判断）
        boolean interactiveMode = System.getenv("INTERACTIVE_MODE") != null ||
                (args.length > 0 && "interactive".equals(args[0]));

        if (interactiveMode) {
            System.out.print("请输入输入CSV文件名（如 translations.csv）: ");
        }
        String inputCsv = scanner.nextLine().trim();

        if (interactiveMode) {
            System.out.print("请输入输出CSV文件名（如 translations_zh.csv）: ");
        }
        String outputCsv = scanner.nextLine().trim();

        if (interactiveMode) {
            System.out.print("请输入阿里云 AccessKeyId: ");
        }
        accessKeyId = scanner.nextLine().trim();

        if (interactiveMode) {
            System.out.print("请输入阿里云 AccessKeySecret: ");
        }
        accessKeySecret = scanner.nextLine().trim();

        // 读取model_id参数（如果提供）
        if (interactiveMode) {
            System.out.print("请输入翻译模型ID（直接回车使用默认27345）: ");
        }
        String modelIdInput = scanner.nextLine().trim();
        if (!modelIdInput.isEmpty()) {
            try {
                modelId = Long.parseLong(modelIdInput);
            } catch (NumberFormatException e) {
                if (interactiveMode) {
                    System.out.println("无效的模型ID，使用默认值27345");
                }
            }
        }

        // 读取起始行参数（如果提供）
        if (interactiveMode) {
            System.out.print("请输入起始行号（直接回车从第0行开始）: ");
        }
        String startLineInput = scanner.nextLine().trim();
        int startLine = 0;
        if (!startLineInput.isEmpty()) {
            try {
                startLine = Integer.parseInt(startLineInput);
            } catch (NumberFormatException e) {
                if (interactiveMode) {
                    System.out.println("无效的起始行号，从第0行开始");
                }
                startLine = 0;
            }
        }

        // 读取翻译字段参数
        if (interactiveMode) {
            System.out.print("请输入翻译字段名（如：text、protected_text，直接回车使用text）: ");
        }
        String translationFieldInput = scanner.nextLine().trim();
        String translationField = "text"; // 默认使用text字段
        if (!translationFieldInput.isEmpty()) {
            translationField = translationFieldInput;
        }

        // 调试输出
        System.out.println("[调试] 接收到的起始行参数: " + startLineInput + " -> " + startLine);
        System.out.println("[调试] 翻译字段: " + translationField);
        scanner.close();

        DefaultProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId, accessKeySecret);
        IAcsClient client = new DefaultAcsClient(profile);

        // 统一文件处理：智能检测恢复模式
        Writer out = null;
        CSVPrinter printer = null;
        boolean isResumeMode = false;

        // 检查输出文件是否存在
        java.io.File outputFile = new java.io.File(outputCsv);
        if (outputFile.exists()) {
            isResumeMode = true;
            System.out.println("检测到已存在的输出文件，将删除最后一行不完整的翻译...");
            removeLastLine(outputCsv);

            // 打开文件用于追加
            out = new OutputStreamWriter(new FileOutputStream(outputCsv, true), StandardCharsets.UTF_8);
            printer = new CSVPrinter(out, CSVFormat.DEFAULT);
        }

        try (
                Reader in = new InputStreamReader(new FileInputStream(inputCsv), StandardCharsets.UTF_8);
                CSVParser parser = new CSVParser(in, CSVFormat.DEFAULT.withFirstRecordAsHeader());) {
            // 先统计总行数
            java.util.List<CSVRecord> records = new java.util.ArrayList<>();
            for (CSVRecord record : parser) {
                records.add(record);
            }
            int totalLines = records.size();

            // 智能恢复：通过key对比确定实际恢复位置
            int actualStartLine = startLine;
            if (isResumeMode) {
                actualStartLine = findActualResumeLine(inputCsv, outputCsv, records);
                if (actualStartLine != startLine) {
                    System.out.println("智能检测：从第 " + actualStartLine + " 行开始恢复翻译（原计划第 " + startLine + " 行）");
                } else {
                    System.out.println("从第 " + startLine + " 行开始恢复翻译，总计 " + totalLines + " 行...");
                }
            } else {
                System.out.println("开始翻译，总计 " + totalLines + " 行...");
                // 创建新的输出文件
                out = new OutputStreamWriter(new FileOutputStream(outputCsv), StandardCharsets.UTF_8);
                printer = new CSVPrinter(out,
                        CSVFormat.DEFAULT.withHeader(appendHeader(parser.getHeaderMap(), "translated")));
            }

            int currentLine = 0;
            for (CSVRecord record : records) {
                // 跳过起始行之前的记录（actualStartLine是数据行号，不包括标题行）
                if (currentLine < actualStartLine) {
                    currentLine++;
                    continue;
                }
                java.util.List<String> originalCols = new java.util.ArrayList<>();
                for (String col : parser.getHeaderNames()) {
                    originalCols.add(record.isMapped(col) ? record.get(col) : "");
                }

                String key = record.isMapped("key") ? record.get("key") : "";
                // 根据参数决定使用哪个字段进行翻译
                String text = record.isMapped(translationField) ? record.get(translationField) : "";
                String zh = "";

                // 优化：统一处理跳过逻辑，减少重复代码
                String skipReason = shouldSkipTranslation(key, text);
                if (skipReason != null) {
                    java.util.List<String> row = new java.util.ArrayList<>(originalCols);

                    // 对于ALIMT保护内容，删除标签只保留内容
                    String processedText = text;
                    if (skipReason.contains("ALIMT")) {
                        processedText = removeAlimtTags(text);
                        System.out.println("跳过翻译并移除ALIMT标签: " + skipReason);
                    } else {
                        System.out.println("跳过翻译: " + skipReason);
                    }

                    row.add(processedText);
                    printer.printRecord(row);
                    continue;
                }

                zh = translatePartWithRetry(client, text, modelId);
                if (zh == null || zh.trim().isEmpty()) {
                    zh = text;
                    System.out.println("翻译失败，使用原文");
                } else {
                    System.out.println("翻译完成");
                }
                java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                row.add(zh);
                printer.printRecord(row);
                // 立即刷新缓冲区确保数据写入文件
                try {
                    printer.flush();
                } catch (Exception e) {
                    System.out.println("[警告] 刷新缓冲区失败: " + e.getMessage());
                }
                // 添加延迟以避免API限制，可以根据需要调整
                try {
                    Thread.sleep(TRANSLATION_DELAY_MS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.out.println("[警告] 翻译过程被中断");
                    break;
                }
                currentLine++;
            }
        } finally {
            // 确保文件被正确关闭
            if (printer != null) {
                try {
                    printer.flush();
                } catch (Exception e) {
                    System.out.println("[警告] 最终刷新缓冲区失败: " + e.getMessage());
                }
            }
            if (out != null) {
                try {
                    out.close();
                } catch (Exception e) {
                    System.out.println("[警告] 关闭文件失败: " + e.getMessage());
                }
            }
        }
    }

    /**
     * 删除CSV文件的最后一行（用于清理不完整的翻译）
     */
    private static void removeLastLine(String filePath) {
        try {
            java.io.File file = new java.io.File(filePath);
            if (!file.exists()) {
                return;
            }

            // 读取所有行
            java.util.List<String> lines = new java.util.ArrayList<>();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    lines.add(line);
                }
            }

            // 删除最后一行
            if (!lines.isEmpty()) {
                lines.remove(lines.size() - 1);

                // 写回文件
                try (BufferedWriter writer = new BufferedWriter(
                        new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8))) {
                    for (String line : lines) {
                        writer.write(line);
                        writer.newLine();
                    }
                }

                System.out.println("已删除最后一行不完整的翻译");
            }
        } catch (Exception e) {
            System.out.println("[警告] 删除最后一行失败: " + e.getMessage());
        }
    }

    /**
     * 翻译文本（使用默认重试次数）
     */
    public static String translatePartWithRetry(IAcsClient client, String part, Long modelId) {
        return translatePartWithRetry(client, part, modelId, DEFAULT_MAX_RETRY);
    }

    /**
     * 翻译文本（指定重试次数）
     */
    public static String translatePartWithRetry(IAcsClient client, String part, Long modelId, int maxRetry) {
        if (part.trim().isEmpty())
            return part;
        for (int attempt = 1; attempt <= maxRetry; attempt++) {
            try {
                String zh = translatePart(client, part, modelId);
                if (zh != null && !zh.trim().isEmpty())
                    return zh;
            } catch (Exception e) {
                // 静默处理错误，避免干扰进度条显示
                // 可以在这里添加日志记录：System.err.println("翻译重试失败: " + e.getMessage());
            }
            try {
                Thread.sleep(RETRY_DELAY_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                System.out.println("[错误] 线程被中断");
                return part;
            }
        }
        return part;
    }

    public static String translatePart(IAcsClient client, String part, Long modelId) throws Exception {
        CommonRequest request = new CommonRequest();
        request.setDomain("automl.cn-hangzhou.aliyuncs.com");
        request.setVersion("2019-07-01");
        request.setAction("PredictMTModel");
        request.setMethod(MethodType.POST);
        request.putQueryParameter("ModelId", modelId.toString());
        request.putQueryParameter("ModelVersion", "V1");
        request.putBodyParameter("Content", part);

        CommonResponse response = client.getCommonResponse(request);
        String data = response.getData();

        String zh = extractResultFromJson(data);
        return zh != null ? zh : part;
    }

    private static String extractResultFromJson(String json) {
        try {
            com.alibaba.fastjson.JSONObject obj = com.alibaba.fastjson.JSON.parseObject(json);

            // 尝试从Data字段提取
            if (obj.containsKey("Data")) {
                Object dataObj = obj.get("Data");
                com.alibaba.fastjson.JSONArray arr = null;

                if (dataObj instanceof String) {
                    arr = com.alibaba.fastjson.JSON.parseArray((String) dataObj);
                } else if (dataObj instanceof com.alibaba.fastjson.JSONArray) {
                    arr = (com.alibaba.fastjson.JSONArray) dataObj;
                }

                if (arr != null && arr.size() > 0) {
                    return arr.getString(0);
                }
            }

            // 尝试从Result字段提取
            String result = obj.getString("Result");
            if (result != null) {
                return result;
            }

            return null;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 通过key对比智能确定恢复翻译的起始行
     */
    private static int findActualResumeLine(String inputCsv, String outputCsv, java.util.List<CSVRecord> inputRecords) {
        try {
            // 读取输出文件中已翻译的key
            java.util.Set<String> translatedKeys = new java.util.HashSet<>();
            try (Reader reader = new InputStreamReader(new FileInputStream(outputCsv), StandardCharsets.UTF_8);
                    CSVParser parser = new CSVParser(reader, CSVFormat.DEFAULT.withFirstRecordAsHeader())) {

                for (CSVRecord record : parser) {
                    if (record.isMapped("key")) {
                        String key = record.get("key");
                        if (key != null && !key.trim().isEmpty()) {
                            translatedKeys.add(key.trim());
                        }
                    }
                }
            }

            // 找到第一个未翻译的key对应的行号
            for (int i = 0; i < inputRecords.size(); i++) {
                CSVRecord record = inputRecords.get(i);
                if (record.isMapped("key")) {
                    String key = record.get("key");
                    if (key != null && !key.trim().isEmpty() && !translatedKeys.contains(key.trim())) {
                        System.out.println("智能检测：找到第一个未翻译的key: " + key + " (第 " + i + " 行)");
                        return i;
                    }
                }
            }

            // 如果所有key都已翻译，返回总行数（表示翻译完成）
            System.out.println("智能检测：所有key都已翻译完成");
            return inputRecords.size();

        } catch (Exception e) {
            System.out.println("[警告] 智能检测失败，使用默认行号: " + e.getMessage());
            return 0;
        }
    }

    private static String[] appendHeader(java.util.Map<String, Integer> headerMap, String newCol) {
        String[] arr = new String[headerMap.size() + 1];
        int i = 0;
        for (String h : headerMap.keySet())
            arr[i++] = h;
        arr[i] = newCol;
        return arr;
    }

}