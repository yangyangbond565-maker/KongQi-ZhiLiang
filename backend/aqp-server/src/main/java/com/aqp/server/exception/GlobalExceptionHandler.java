package com.aqp.server.exception;

import com.aqp.common.BizException;
import com.aqp.common.Result;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 统一异常处理：数据库异常不把堆栈返回给前端。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BizException.class)
    public Result<Void> handleBiz(BizException ex) {
        return Result.error(ex.getCode(), ex.getMessage());
    }

    @ExceptionHandler(DataAccessException.class)
    public Result<Void> handleDb(DataAccessException ex) {
        log.error("数据库访问失败", ex);
        return Result.error(500, "数据库访问失败，请检查数据库服务");
    }

    @ExceptionHandler(Exception.class)
    public Result<Void> handleOther(Exception ex) {
        log.error("未处理异常", ex);
        return Result.error(500, "服务器内部错误");
    }
}
