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
    static String accessKeyId = null;
    static String accessKeySecret = null;
    static Long modelId = 27345L;

    public static void main(String[] args) throws Exception {
        Scanner scanner = new Scanner(System.in, StandardCharsets.UTF_8);

        System.out.print("请输入输入CSV文件名（如 translations.csv）: ");
        String inputCsv = scanner.nextLine().trim();
        System.out.print("请输入输出CSV文件名（如 translations_zh.csv）: ");
        String outputCsv = scanner.nextLine().trim();

        System.out.print("请输入阿里云 AccessKeyId: ");
        accessKeyId = scanner.nextLine().trim();
        System.out.print("请输入阿里云 AccessKeySecret: ");
        accessKeySecret = scanner.nextLine().trim();
        scanner.close();

        DefaultProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId, accessKeySecret);
        IAcsClient client = new DefaultAcsClient(profile);

        try (
            Reader in = new InputStreamReader(new FileInputStream(inputCsv), StandardCharsets.UTF_8);
            Writer out = new OutputStreamWriter(new FileOutputStream(outputCsv), StandardCharsets.UTF_8);
            CSVParser parser = new CSVParser(in, CSVFormat.DEFAULT.withFirstRecordAsHeader());
            CSVPrinter printer = new CSVPrinter(out, CSVFormat.DEFAULT.withHeader(appendHeader(parser.getHeaderMap(), "translated")));
        ) {
            // 先统计总行数
            java.util.List<CSVRecord> records = new java.util.ArrayList<>();
            for (CSVRecord record : parser) {
                records.add(record);
            }
            int totalLines = records.size();
            
            System.out.println("开始翻译，总计 " + totalLines + " 行...");
            
            for (CSVRecord record : records) {
                java.util.List<String> originalCols = new java.util.ArrayList<>();
                for (String col : parser.getHeaderNames()) {
                    originalCols.add(record.isMapped(col) ? record.get(col) : "");
                }

                String key = record.isMapped("key") ? record.get("key") : "";
                String text = record.isMapped("text") ? record.get("text") : "";
                String zh = "";

                if (key.trim().isEmpty() || text.trim().isEmpty()) {
                    java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                    row.add("");
                    printer.printRecord(row);
                    System.out.println("跳过空行");
                    continue;
                }
                if (text.matches("(\\s*\\[[^\\]]+\\]\\s*)+")) {
                    java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                    row.add(text);
                    printer.printRecord(row);
                    System.out.println("跳过占位符");
                    continue;
                }

                zh = aliyunTranslateCustom(client, text, modelId);
                if (zh == null || zh.trim().isEmpty()) {
                    zh = text;
                    System.out.println("翻译失败，使用原文");
                } else {
                    System.out.println("翻译完成");
                }
                java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                row.add(zh);
                printer.printRecord(row);
                // 添加延迟以避免API限制，可以根据需要调整
                try {
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.out.println("[警告] 翻译过程被中断");
                    break;
                }
            }
        }
    }

    public static String aliyunTranslateCustom(IAcsClient client, String text, Long modelId) {
        String protectedText = text;
        String prefix = null;

        java.util.regex.Matcher prefixMatcher = java.util.regex.Pattern.compile("^([a-zA-Z0-9_]+->)").matcher(protectedText);
        if (prefixMatcher.find()) {
            prefix = prefixMatcher.group(1);
            protectedText = protectedText.replaceFirst(java.util.regex.Pattern.quote(prefix), "{{PREFIX}}");
        }

        java.util.List<String> placeholders = new java.util.ArrayList<>();
        int idx = 1;
        // 首先将真实换行符转换为转义换行符
        protectedText = protectedText.replace("\r\n", "\\n").replace("\n", "\\n");
        
        String[] patterns = {
            "\\\\n",                             // \n 换行符（标准化后的格式）
            "\\[[^\\]]+\\]",                    // [xxx]
            "\\{\\d+\\}",                        // {0}, {1}
            "%[sdif]",                            // %s, %d, %i, %f
            "</?[^>]+>",                          // <color> 或 <br>
            "[a-zA-Z_][a-zA-Z0-9_]*\\([^)]*\\)", // 函数调用，如 bad_opinion_rapist(...)
            "->\\[[^\\]]+\\]",                    // ->[结果]
            "\\bpawn\\b",                        // pawn 游戏术语
        };
        
        for (String pat : patterns) {
            java.util.regex.Matcher m = java.util.regex.Pattern.compile(pat).matcher(protectedText);
            StringBuffer sb = new StringBuffer();
            while (m.find()) {
                String ph = m.group();
                // 跳过已经保护的ALIMT标签
                if (ph.contains("ALIMT")) {
                    continue;
                }
                placeholders.add(ph);
                String placeholder = "(PH_" + idx++ + ")"; // 加括号更保险
                String alimtTag = "<ALIMT >" + placeholder + "</ALIMT>";
                m.appendReplacement(sb, alimtTag);
            }
            m.appendTail(sb);
            protectedText = sb.toString();
        }

        String translatedText = translatePartWithRetry(client, protectedText, modelId, 2);
        if (prefix != null) translatedText = translatedText.replace("{{PREFIX}}", prefix);
        
        // 根据占位符顺序恢复保护的内容
        for (int i = 0; i < placeholders.size(); i++) {
            String original = placeholders.get(i);
            String placeholder = "(PH_" + (i + 1) + ")";
            
            if (translatedText.contains(placeholder)) {
                translatedText = translatedText.replace(placeholder, original);
            }
        }
        return translatedText;
    }

    public static String translatePartWithRetry(IAcsClient client, String part, Long modelId, int maxRetry) {
        if (part.trim().isEmpty()) return part;
        for (int attempt = 1; attempt <= maxRetry; attempt++) {
            try {
                String zh = translatePart(client, part, modelId);
                if (zh != null && !zh.trim().isEmpty()) return zh;
            } catch (Exception e) {
                // 静默处理错误，避免干扰进度条显示
            }
            try { 
                Thread.sleep(2000); 
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

    private static String[] appendHeader(java.util.Map<String, Integer> headerMap, String newCol) {
        String[] arr = new String[headerMap.size() + 1];
        int i = 0;
        for (String h : headerMap.keySet()) arr[i++] = h;
        arr[i] = newCol;
        return arr;
    }
    
}