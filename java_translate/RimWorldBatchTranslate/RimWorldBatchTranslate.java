package com.daytranslation;

import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.profile.DefaultProfile;
import org.apache.commons.csv.*;

import java.io.*;
import java.util.regex.*;
import java.util.Scanner;

public class RimWorldBatchTranslate {
    // 阿里云认证信息（运行时输入）
    static String accessKeyId = null;
    static String accessKeySecret = null;
    static Long modelId = 27345L; // 定制模型ID

    // 占位符正则
    static Pattern placeholderPattern = Pattern.compile("(\\[[^\\]]+\\])");

    public static void main(String[] args) throws Exception {
        // 使用Scanner处理输入，设置UTF-8编码
        Scanner scanner = new Scanner(System.in, "UTF-8");
        
        System.out.print("请输入输入CSV文件名（如 translations.csv）: ");
        String inputCsv = scanner.nextLine().trim();
        System.out.print("请输入输出CSV文件名（如 translations_zh.csv）: ");
        String outputCsv = scanner.nextLine().trim();

        // 交互式输入阿里云认证信息
        System.out.print("请输入阿里云 AccessKeyId: ");
        accessKeyId = scanner.nextLine().trim();
        System.out.print("请输入阿里云 AccessKeySecret: ");
        accessKeySecret = scanner.nextLine().trim();
        
        scanner.close();

        // 初始化阿里云 OpenAPI 通用 SDK
        DefaultProfile profile = DefaultProfile.getProfile(
            "cn-hangzhou", accessKeyId, accessKeySecret);
        IAcsClient client = new DefaultAcsClient(profile);

        try (
            Reader in = new InputStreamReader(new FileInputStream(inputCsv), "UTF-8");
            Writer out = new OutputStreamWriter(new FileOutputStream(outputCsv), "UTF-8");
            CSVParser parser = new CSVParser(in, CSVFormat.DEFAULT.withFirstRecordAsHeader());
            CSVPrinter printer = new CSVPrinter(out, CSVFormat.DEFAULT
                    .withHeader(appendHeader(parser.getHeaderMap(), "translated")))
        ) {
            int lineNum = 1;
            for (CSVRecord record : parser) {
                // 动态获取所有原有列的内容
                java.util.List<String> originalCols = new java.util.ArrayList<>();
                for (String col : record.getParser().getHeaderNames()) {
                    originalCols.add(record.isMapped(col) ? record.get(col) : "");
                }
                // 获取 key 和 text 字段用于逻辑判断
                String key = record.isMapped("key") ? record.get("key") : "";
                String text = record.isMapped("text") ? record.get("text") : "";
                String zh = "";

                if (key.trim().isEmpty() || text.trim().isEmpty()) {
                    // 原有列+空翻译
                    java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                    row.add("");
                    printer.printRecord(row);
                    System.out.println("[调试] 跳过第" + lineNum + "行：" + key + "," + text);
                    lineNum++;
                    continue;
                }
                if (text.matches("(\\s*\\[[^\\]]+\\]\\s*)+")) {
                    // 原有列+原文（全占位符不翻译）
                    java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                    row.add(text);
                    printer.printRecord(row);
                    System.out.println("[调试] 跳过第" + lineNum + "行（全占位符不翻译）：" + text);
                    lineNum++;
                    continue;
                }

                zh = aliyunTranslateCustom(client, text, modelId);
                if (zh == null || zh.trim().isEmpty()) {
                    System.out.println("[调试] 第" + lineNum + "行翻译失败，已暂停。原文：" + text + "  翻译：" + zh);
                    break;
                }
                // 原有列+翻译
                java.util.List<String> row = new java.util.ArrayList<>(originalCols);
                row.add(zh);
                printer.printRecord(row);
                System.out.println("[调试] 第" + lineNum + "行翻译完成：原文：" + text + "  =>  翻译：" + zh);
                lineNum++;
                Thread.sleep(500); // 防止QPS超限
            }
        }
    }


    // 占位符保护+调用阿里云定制模型（通用SDK实现）
    public static String aliyunTranslateCustom(IAcsClient client, String text, Long modelId) {
        Matcher matcher = placeholderPattern.matcher(text);
        StringBuffer sb = new StringBuffer();
        int lastEnd = 0;
        while (matcher.find()) {
            // 翻译前面的正文
            if (matcher.start() > lastEnd) {
                String part = text.substring(lastEnd, matcher.start());
                String zh = translatePart(client, part, modelId);
                sb.append(zh);
            }
            // 保留占位符
            sb.append(matcher.group());
            lastEnd = matcher.end();
        }
        // 处理最后一段正文
        if (lastEnd < text.length()) {
            String part = text.substring(lastEnd);
            String zh = translatePart(client, part, modelId);
            sb.append(zh);
        }
        return sb.toString();
    }

    // 单段正文调用阿里云定制模型（通用SDK实现）
    public static String translatePart(IAcsClient client, String part, Long modelId) {
        if (part.trim().isEmpty()) return part;
        try {
            CommonRequest request = new CommonRequest();
            // 以下方法已弃用，但为兼容阿里云API，保留使用
            request.setDomain("automl.cn-hangzhou.aliyuncs.com"); // deprecated
            request.setVersion("2019-07-01"); // deprecated
            request.setAction("PredictMTModel"); // deprecated
            request.setMethod(MethodType.POST); // deprecated
            request.putQueryParameter("ModelId", modelId.toString());
            request.putQueryParameter("ModelVersion", "V1"); // 如有需要可调整
            request.putBodyParameter("Content", part);

            CommonResponse response = client.getCommonResponse(request);
            String data = response.getData();
            System.out.println("[API返回] " + data); // 打印原始返回内容
            // 解析返回的JSON，提取Result字段
            String zh = extractResultFromJson(data);
            if (zh == null || zh.trim().isEmpty()) {
                System.out.println("[警告] 翻译结果为空，原文：" + part);
            }
            return zh != null ? zh : part;
        } catch (Exception e) {
            e.printStackTrace();
            return part;
        }
    }

    // 提取Result字段（需fastjson依赖）
   private static String extractResultFromJson(String json) {
    try {
        com.alibaba.fastjson.JSONObject obj = com.alibaba.fastjson.JSON.parseObject(json);
        // 兼容 {"Data":"[\"xxx\"]"} 或 {"Data":["xxx"]} 或 {"Result":"xxx"}
        if (obj.containsKey("Data")) {
            Object dataObj = obj.get("Data");
            if (dataObj instanceof String) {
                // Data 是字符串形式的数组
                com.alibaba.fastjson.JSONArray arr = com.alibaba.fastjson.JSON.parseArray((String) dataObj);
                if (arr.size() > 0) return arr.getString(0);
            } else if (dataObj instanceof com.alibaba.fastjson.JSONArray) {
                com.alibaba.fastjson.JSONArray arr = (com.alibaba.fastjson.JSONArray) dataObj;
                if (arr.size() > 0) return arr.getString(0);
            }
        }
        return obj.getString("Result");
    } catch (Exception e) {
        return null;
    }
}

    // 工具：追加"翻译"列头
    private static String[] appendHeader(java.util.Map<String, Integer> headerMap, String newCol) {
        String[] arr = new String[headerMap.size() + 1];
        int i = 0;
        for (String h : headerMap.keySet()) arr[i++] = h;
        arr[i] = newCol;
        return arr;
    }
}