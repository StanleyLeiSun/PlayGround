package com.kidscheck.app.util

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * 全局认证事件总线，用于处理 Token 过期等认证失败情况
 */
object AuthEventBus {
    private val _authEvents = MutableSharedFlow<AuthEvent>()
    val authEvents = _authEvents.asSharedFlow()

    suspend fun emit(event: AuthEvent) {
        _authEvents.emit(event)
    }
}

sealed class AuthEvent {
    /** Token 过期或无效，需要重新登录 */
    object TokenExpired : AuthEvent()
}
