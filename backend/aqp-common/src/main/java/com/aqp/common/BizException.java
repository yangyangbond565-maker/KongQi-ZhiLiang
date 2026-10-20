package com.aqp.common;

/**
 * 业务异常：参数不合法等可预期错误。
 */
public class BizException extends RuntimeException {

    private final int code;

    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() {
        return code;
    }
}
